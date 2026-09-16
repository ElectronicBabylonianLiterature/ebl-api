"""MIME policy for media representations.

SVG is not a third media type: a hand copy is `MediaType.COPY` whose original
carries `image/svg+xml`. The policy this module serves, enforced by
`Media.representations`:

- `PHOTO` originals accept only supported raster MIME types.
- `COPY` originals accept supported raster MIME types or `image/svg+xml`.
- Display and thumbnail representations accept only supported raster MIME
  types, whatever the original is. An SVG original is therefore previewed as
  raster and stays download-only.

Two obligations fall on the infrastructure that will store binaries, and cannot
be enforced here because this layer never sees bytes: the MIME type must be
determined server-side by inspecting content — a filename extension is never
trusted — and SVG must be sanitized with a safe XML parser before storage,
rejecting or stripping scripts, event attributes, external references,
`foreignObject`, and dangerous processing instructions or entity declarations.
No sanitizer is introduced by the contracts in this module.
"""

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
