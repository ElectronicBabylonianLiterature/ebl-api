import hashlib
import warnings
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, cast

from PIL import Image

from ebl.media.domain import MediaRepresentation
from ebl.media.infrastructure.media_webp import webp_dimensions

READ_CHUNK_SIZE = 65536
MAX_RASTER_PIXELS = 40_000_000


def raster_mime_type(header: bytes) -> str:
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Only JPEG, PNG, and WebP raster bytes can be stored.")


def verified_content(
    content: BinaryIO,
    representation: MediaRepresentation,
    max_file_size: int,
    *,
    inspect_image: bool = True,
) -> BinaryIO:
    if representation.file_size > max_file_size:
        raise ValueError("Media representation exceeds the file size limit.")
    temporary = cast(BinaryIO, SpooledTemporaryFile(max_size=8 * 1024 * 1024))
    try:
        checksum = hashlib.sha256()
        count = 0
        while chunk := content.read(READ_CHUNK_SIZE):
            count += len(chunk)
            if count > max_file_size or count > representation.file_size:
                raise ValueError("Media representation exceeds its declared size.")
            checksum.update(chunk)
            temporary.write(chunk)
        if count != representation.file_size:
            raise ValueError("Media representation byte count does not match.")
        expected_checksum = representation.checksum
        if expected_checksum and checksum.hexdigest() != expected_checksum.value:
            raise ValueError("Media representation checksum does not match.")
        temporary.seek(0)
        if raster_mime_type(temporary.read(12)) != representation.mime_type:
            raise ValueError("Media representation MIME type does not match its bytes.")
        temporary.seek(0)
        if inspect_image:
            _verify_dimensions(temporary, representation)
        temporary.seek(0)
        return temporary
    except BaseException:
        temporary.close()
        raise


def _verify_dimensions(content: BinaryIO, representation: MediaRepresentation) -> None:
    dimensions = webp_dimensions(content)
    if dimensions and dimensions[0] * dimensions[1] > MAX_RASTER_PIXELS:
        raise ValueError("Media representation exceeds the pixel limit.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(content) as image:
            if image.width * image.height > MAX_RASTER_PIXELS:
                raise ValueError("Media representation exceeds the pixel limit.")
            if image.size != (representation.width, representation.height):
                raise ValueError(
                    "Media representation dimensions do not match its bytes."
                )
            if image.format == "JPEG":
                image.load()
            else:
                image.verify()
