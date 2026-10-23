import hashlib
import io
import warnings
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, Iterator, Mapping, cast

from gridfs import GridFS
from gridfs.errors import CorruptGridFile, NoFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pymongo.database import Database

from ebl.media.application.backfill_plan import BackfillPolicy, SourceRejected
from ebl.media.domain import MediaChecksum, MediaRepresentation
from ebl.media.infrastructure.backfill_jpeg import inspect_jpeg
from ebl.media.infrastructure.backfill_jpeg_segments import exif_evidence
from ebl.media.infrastructure.media_webp import webp_dimensions


@contextmanager
def source_content(
    database: Database, document: Mapping, policy: BackfillPolicy
) -> Iterator[BinaryIO]:
    length = document.get("length")
    if (
        isinstance(length, bool)
        or not isinstance(length, int)
        or not 0 < length <= policy.max_file_size
    ):
        raise SourceRejected("blocked", "invalid-or-excessive-byte-length")
    try:
        with GridFS(database, "photos").get(document["_id"]) as source:
            with SpooledTemporaryFile(max_size=8_388_608, mode="w+b") as content:
                total = 0
                while chunk := source.read(1_048_576):
                    total += len(chunk)
                    if total > length:
                        raise SourceRejected("blocked", "declared-length-mismatch")
                    content.write(chunk)
                if total != length:
                    raise SourceRejected("blocked", "declared-length-mismatch")
                content.seek(0)
                yield cast(BinaryIO, content)
    except (NoFile, CorruptGridFile) as error:
        raise SourceRejected("blocked", "unavailable-original") from error


def checksum(content: BinaryIO) -> str:
    content.seek(0)
    digest = hashlib.sha256()
    while chunk := content.read(1_048_576):
        digest.update(chunk)
    content.seek(0)
    return digest.hexdigest()


def inspect_image(
    content: BinaryIO, length: int, policy: BackfillPolicy
) -> tuple[MediaRepresentation, dict[str, str]]:
    digest = checksum(content)
    if content.read(2) == b"\xff\xd8":
        width, height, evidence = inspect_jpeg(content, length)
        if width * height > policy.max_pixels:
            return MediaRepresentation(
                "image/jpeg", width, height, length, MediaChecksum(value=digest)
            ), evidence
    content.seek(0)
    try:
        dimensions = webp_dimensions(content)
        if dimensions is not None and dimensions[0] * dimensions[1] > policy.max_pixels:
            raise SourceRejected("review", "pixel-inspection-limit")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(content) as image:
                mime_type = Image.MIME.get(image.format or "", "")
                if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
                    raise SourceRejected("blocked", "unsupported-mime-type")
                if image.width * image.height > policy.max_pixels:
                    raise SourceRejected("review", "pixel-inspection-limit")
                if getattr(image, "is_animated", False):
                    raise SourceRejected("review", "animated-original")
                representation = MediaRepresentation(
                    mime_type,
                    image.width,
                    image.height,
                    length,
                    MediaChecksum(value=digest),
                )
                evidence = exif_evidence(image.getexif())
                image.load()
                return representation, evidence
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise SourceRejected("review", "pixel-inspection-limit") from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        if isinstance(error, SourceRejected):
            raise
        raise SourceRejected("blocked", "malformed-original") from error
    finally:
        if not content.closed:
            content.seek(0)


def preview_bytes(content: BinaryIO, size: int) -> bytes:
    content.seek(0)
    try:
        with Image.open(content) as source:
            with ImageOps.exif_transpose(source) as oriented:
                oriented.thumbnail((size, size))
                with oriented.convert("RGB") as image:
                    output = io.BytesIO()
                    image.save(output, format="JPEG", quality=85, optimize=True)
                    return output.getvalue()
    except (OSError, ValueError) as error:
        raise SourceRejected("blocked", "preview-decode-failed") from error
