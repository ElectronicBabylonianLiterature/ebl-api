from io import BytesIO

import attr
import pytest

from ebl.media.domain import MediaChecksum
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
