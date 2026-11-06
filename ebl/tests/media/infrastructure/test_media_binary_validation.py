from io import BytesIO
from struct import pack
from zlib import crc32

import attr
import pytest
from PIL import Image

from ebl.media.domain import MediaChecksum
from ebl.media.infrastructure import media_binary_validation
from ebl.media.infrastructure.media_binary_validation import (
    raster_mime_type,
    verified_content,
)
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)


@pytest.mark.parametrize(
    "format_, mime_type",
    [
        ("JPEG", "image/jpeg"),
        ("PNG", "image/png"),
        ("WEBP", "image/webp"),
    ],
)
def test_actual_mime_and_dimensions(format_: str, mime_type: str) -> None:
    content = image_bytes(format_)
    with verified_content(
        BytesIO(content), image_representation(content, mime_type), 10000
    ) as verified:
        assert verified.read() == content


@pytest.mark.parametrize(
    "change, message",
    [
        ({"file_size": 1}, "exceeds"),
        ({"file_size": 1000}, "byte count"),
        ({"checksum": MediaChecksum(value="0" * 64)}, "checksum"),
        ({"mime_type": "image/jpeg"}, "MIME"),
        ({"width": 10}, "dimensions"),
    ],
)
def test_binary_metadata_must_match(change: dict, message: str) -> None:
    representation = attr.evolve(image_representation(), **change)
    with pytest.raises(ValueError, match=message):
        verified_content(BytesIO(image_bytes()), representation, 2000)


def test_declared_size_limit_is_enforced_before_read() -> None:
    with pytest.raises(ValueError, match="limit"):
        verified_content(BytesIO(image_bytes()), image_representation(), 1)


def test_unsupported_bytes_and_svg_are_rejected() -> None:
    for content in (b"not an image", b"<svg />", b"RIFFinvalid"):
        with pytest.raises(ValueError, match="Only JPEG"):
            raster_mime_type(content)


def oversized_png() -> bytes:
    content = bytearray(image_bytes())
    content[16:24] = pack(">II", media_binary_validation.MAX_RASTER_PIXELS + 1, 1)
    content[29:33] = pack(">I", crc32(bytes(content[12:29])))
    return bytes(content)


def test_owned_pixel_bound_survives_disabled_pillow_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", None)
    content = oversized_png()
    representation = attr.evolve(
        image_representation(content),
        width=media_binary_validation.MAX_RASTER_PIXELS + 1,
        height=1,
    )
    with pytest.raises(ValueError, match="pixel limit"):
        verified_content(BytesIO(content), representation, 2000)


def test_owned_pixel_bound_includes_exact_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", None)
    monkeypatch.setattr(media_binary_validation, "MAX_RASTER_PIXELS", 48)
    with verified_content(
        BytesIO(image_bytes()), image_representation(), 2000
    ) as content:
        assert content.read() == image_bytes()


def test_borrowed_validation_does_not_decode_large_images() -> None:
    content = oversized_png()
    with verified_content(
        BytesIO(content), image_representation(content), 2000, inspect_image=False
    ) as validated:
        assert validated.read() == content
