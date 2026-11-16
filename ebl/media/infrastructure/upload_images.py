"""Bounded raster uploads, using the owned media store and preview conventions.

Original bytes (including any EXIF attribution evidence) are retained unchanged.
Derivatives use the same JPEG sizes, quality and EXIF orientation handling as
the legacy migration preview writer; no migration code or startup job is needed.
"""

import hashlib
import os
import warnings
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from functools import lru_cache
from tempfile import SpooledTemporaryFile
from threading import BoundedSemaphore, Lock
from typing import BinaryIO, Callable, Iterator, cast

from PIL import Image, ImageOps

from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import StoredMediaRepresentations
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.domain import MediaChecksum, MediaId, MediaRepresentation, ThumbnailSize
from ebl.media.infrastructure.media_binary_validation import raster_mime_type
from ebl.media.infrastructure.media_webp import webp_dimensions
from ebl.media.infrastructure.prepared_upload import PreparedUpload, UploadContent
from ebl.media.infrastructure.upload_previews import (
    LANCZOS_RESAMPLING,
    eight_bit,
    preview,
)

DECODER_CONFIGURATION_LOCK = Lock()
CHUNK_SIZE = 65_536
THUMBNAIL_PIXELS = (
    (ThumbnailSize.SMALL, 240),
    (ThumbnailSize.MEDIUM, 480),
    (ThumbnailSize.LARGE, 720),
)


class UploadValidationError(ValueError):
    """The supplied content is not a permitted, complete static raster image."""


class UploadTooLargeError(UploadValidationError):
    """The original exceeds the configured transport byte limit."""


class UploadBusyError(RuntimeError):
    """The bounded decoder pool is busy; the same request can be retried."""


@lru_cache(maxsize=1)
def _decoder_slots() -> BoundedSemaphore:
    count = int(os.environ.get("MEDIA_UPLOAD_DECODE_SLOTS", "1"))
    if count not in (1, 2):
        raise ValueError("MEDIA_UPLOAD_DECODE_SLOTS must be 1 or 2.")
    return BoundedSemaphore(count)


@dataclass(frozen=True)
class UploadLimits:
    max_bytes: int = 25 * 1024 * 1024
    max_pixels: int = 40_000_000
    max_dimension: int = 20_000
    spool_memory_bytes: int = 1024 * 1024

    def __post_init__(self) -> None:
        for value in (
            self.max_bytes,
            self.max_pixels,
            self.max_dimension,
            self.spool_memory_bytes,
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError("Upload limits must be positive integers.")
        if self.max_pixels > 40_000_000:
            raise ValueError("Upload pixel limit exceeds the owned-store safety limit.")


DEFAULT_UPLOAD_LIMITS = UploadLimits()


def write_prepared(
    prepared: PreparedUpload,
    store: MediaRepresentationStore,
    media_id: MediaId,
    on_staged: Callable[[StoredRepresentationHandle], None] | None = None,
) -> StoredMediaRepresentations:
    return prepared.store(store, media_id, on_staged)


def _spool(
    source: BinaryIO, target: BinaryIO, content_length: int | None, limits: UploadLimits
) -> tuple[int, MediaChecksum]:
    if content_length is not None:
        if (
            isinstance(content_length, bool)
            or not isinstance(content_length, int)
            or content_length <= 0
        ):
            raise UploadValidationError("Upload content length must be positive.")
        if content_length > limits.max_bytes:
            raise UploadTooLargeError("Image exceeds the upload size limit.")
    digest = hashlib.sha256()
    length = 0
    while chunk := source.read(min(CHUNK_SIZE, limits.max_bytes - length + 1)):
        length += len(chunk)
        if length > limits.max_bytes:
            raise UploadTooLargeError("Image exceeds the upload size limit.")
        if content_length is not None and length > content_length:
            raise UploadValidationError("Upload length does not match Content-Length.")
        target.write(chunk)
        digest.update(chunk)
    if length == 0 or (content_length is not None and length != content_length):
        raise UploadValidationError("Upload length does not match Content-Length.")
    target.seek(0)
    return length, MediaChecksum(value=digest.hexdigest())


def _check_geometry(width: int, height: int, limits: UploadLimits) -> None:
    if (
        width <= 0
        or height <= 0
        or max(width, height) > limits.max_dimension
        or width * height > limits.max_pixels
    ):
        raise UploadValidationError("Image exceeds the dimension or pixel limit.")


def _inspect(
    content: BinaryIO, length: int, checksum: MediaChecksum, limits: UploadLimits
) -> MediaRepresentation:
    content.seek(0)
    mime_type = raster_mime_type(content.read(12))
    content.seek(0)
    dimensions = webp_dimensions(content)
    if dimensions is not None:
        _check_geometry(*dimensions, limits)
    with Image.open(content) as image:
        if Image.MIME.get(image.format or "") != mime_type:
            raise UploadValidationError("Image type does not match its binary content.")
        _check_geometry(image.width, image.height, limits)
        if getattr(image, "n_frames", 1) != 1 or getattr(image, "is_animated", False):
            raise UploadValidationError(
                "Animated and multi-frame uploads are unsupported."
            )
        representation = MediaRepresentation(
            mime_type, image.width, image.height, length, checksum
        )
        image.verify()
    content.seek(0)
    return representation


@contextmanager
def prepare_upload(
    content: BinaryIO,
    *,
    content_length: int | None = None,
    declared_mime_type: str | None = None,
    limits: UploadLimits = DEFAULT_UPLOAD_LIMITS,
) -> Iterator[PreparedUpload]:
    """Spool a bounded request and fully decode it before any storage write.

    Generated derivatives are oriented static JPEGs with bounded dimensions.
    All temporary streams are closed on success, validation failure or cancel.
    File names, browser MIME and EXIF are never evidence of submission rights.
    """
    with ExitStack() as stack:
        original = cast(
            BinaryIO,
            stack.enter_context(
                SpooledTemporaryFile(max_size=limits.spool_memory_bytes, mode="w+b")
            ),
        )
        length, checksum = _spool(content, original, content_length, limits)
        with DECODER_CONFIGURATION_LOCK:
            slots = _decoder_slots()
        if not slots.acquire(blocking=False):
            raise UploadBusyError(
                "Image processing is busy. Retry this upload shortly."
            )
        stack.callback(slots.release)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                representation = _inspect(original, length, checksum, limits)
                if (
                    declared_mime_type is not None
                    and declared_mime_type.split(";", 1)[0].strip().lower()
                    != representation.mime_type
                ):
                    raise UploadValidationError(
                        "Content-Type does not match the image's binary content."
                    )
                with Image.open(original) as source:
                    source.load()
                    oriented = ImageOps.exif_transpose(source)
                with eight_bit(oriented) as raster:
                    raster.thumbnail((2560, 2560), LANCZOS_RESAMPLING)
                    display = preview(raster, 2560, stack)
                    thumbnails = tuple(
                        (size, preview(raster, pixels, stack))
                        for size, pixels in THUMBNAIL_PIXELS
                    )
        except (UploadValidationError, MemoryError):
            raise
        except Exception as error:
            raise UploadValidationError(
                "Invalid or unsafe raster image content."
            ) from error
        original.seek(0)
        yield PreparedUpload(
            UploadContent(representation, original), display, thumbnails
        )
