from io import BytesIO

import pytest
from PIL import Image

from ebl.media.infrastructure.media_webp import webp_dimensions
from ebl.media.infrastructure.media_binary_validation import verified_content
from ebl.tests.media.infrastructure.persistence_helpers import image_representation


def webp_content(kind: str) -> bytes:
    with BytesIO() as content:
        with Image.new("RGBA", (8, 6), (255, 0, 0, 128)) as image:
            if kind == "animated":
                with Image.new("RGBA", (8, 6), "blue") as frame:
                    image.save(content, "WEBP", save_all=True, append_images=[frame])
            else:
                image.save(content, "WEBP", lossless=kind == "lossless")
        return content.getvalue()


@pytest.mark.parametrize("kind", ["alpha", "lossless", "animated"])
def test_real_webp_geometry_and_owned_validation(kind: str) -> None:
    content = webp_content(kind)
    stream = BytesIO(content)
    stream.seek(7)
    assert webp_dimensions(stream) == (8, 6)
    assert stream.tell() == 7
    with verified_content(
        BytesIO(content), image_representation(content, "image/webp"), 10000
    ) as verified:
        assert verified.read() == content


def container(chunk_type: bytes, payload: bytes) -> bytes:
    body = chunk_type + len(payload).to_bytes(4, "little") + payload
    body += b"\0" * (len(payload) % 2)
    return b"RIFF" + (len(body) + 4).to_bytes(4, "little") + b"WEBP" + body


@pytest.mark.parametrize(
    "chunk_type,payload,expected",
    [
        (b"VP8X", b"\0" * 4 + b"\xff" * 6, (16777216, 16777216)),
        (b"VP8L", b"\x2f\xff\xff\xff\x0f", (16384, 16384)),
        (b"VP8 ", b"\0" * 3 + b"\x9d\x01\x2a\xff\xff\xff\xff", (16383, 16383)),
    ],
    ids=["extended", "lossless", "lossy"],
)
def test_extreme_dimensions_require_no_decoder(
    chunk_type: bytes, payload: bytes, expected: tuple[int, int]
) -> None:
    assert webp_dimensions(BytesIO(container(chunk_type, payload))) == expected


@pytest.mark.parametrize(
    "content",
    [
        b"RIFF\x04\0\0\0WEBP",
        b"RIFF\x64\0\0\0WEBPVP8X\x0a\0\0\0" + b"\0" * 10,
        b"RIFF\x15\0\0\0WEBPVP8X\x0a\0\0\0" + b"\0" * 10,
        b"RIFF\x14\0\0\0WEBPVP8X\x0a\0\0\0" + b"\0" * 10,
        container(b"VP8X", b"\0" * 9),
        container(b"VP8L", b"\x2f\0\0\0\xe0"),
        container(b"VP8L", b"\0" * 5),
        container(b"VP8 ", b"\0" * 10),
        container(b"VP8 ", b"\0" * 3 + b"\x9d\x01\x2a" + b"\0" * 4),
        container(b"????", b"\0" * 10),
    ],
    ids=[
        "short",
        "truncated",
        "odd-length",
        "chunk-overflow",
        "short-extended",
        "lossless-version",
        "lossless-signature",
        "lossy-signature",
        "zero-size",
        "unknown-chunk",
    ],
)
def test_malformed_headers_are_rejected_and_position_restored(content: bytes) -> None:
    stream = BytesIO(content)
    stream.seek(2)
    with pytest.raises(ValueError, match="Malformed WebP"):
        webp_dimensions(stream)
    assert stream.tell() == 2


def test_non_webp_retains_position() -> None:
    stream = BytesIO(b"not WebP")
    stream.seek(2)
    assert webp_dimensions(stream) is None
    assert stream.tell() == 2


def test_header_reads_are_bounded() -> None:
    class BoundedContent(BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            assert size == 30
            return super().read(size)

    payload = b"\0" * 10
    stream = BoundedContent(container(b"VP8X", payload) + b"x" * 10000)
    assert webp_dimensions(stream) == (1, 1)
