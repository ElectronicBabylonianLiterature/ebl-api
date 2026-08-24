from typing import FrozenSet

JPEG = "image/jpeg"
PNG = "image/png"
WEBP = "image/webp"
SVG = "image/svg+xml"

PAINTABLE_IMAGE_FORMATS: FrozenSet[str] = frozenset({JPEG, PNG, WEBP})


def is_paintable(mime_type: str) -> bool:
    return mime_type in PAINTABLE_IMAGE_FORMATS
