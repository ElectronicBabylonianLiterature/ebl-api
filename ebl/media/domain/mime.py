SVG_MIME_TYPE = "image/svg+xml"
SUPPORTED_RASTER_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


def normalize_mime_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def is_supported_raster_mime_type(value: str) -> bool:
    return normalize_mime_type(value) in SUPPORTED_RASTER_MIME_TYPES


def is_svg_mime_type(value: str) -> bool:
    return normalize_mime_type(value) == SVG_MIME_TYPE
