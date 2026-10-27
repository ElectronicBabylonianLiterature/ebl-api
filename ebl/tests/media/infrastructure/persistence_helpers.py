from hashlib import sha256
from io import BytesIO

from PIL import Image

from ebl.media.domain import MediaChecksum, MediaRepresentation


def image_bytes(format_: str = "PNG") -> bytes:
    with BytesIO() as content:
        Image.new("RGB", (8, 6), "red").save(content, format=format_)
        return content.getvalue()


def image_representation(
    content: bytes | None = None, mime_type: str = "image/png"
) -> MediaRepresentation:
    actual = image_bytes() if content is None else content
    return MediaRepresentation(
        mime_type, 8, 6, len(actual), MediaChecksum(value=sha256(actual).hexdigest())
    )
