import hashlib
import struct
import zlib
from io import BytesIO
from typing import Literal, Tuple, cast
from zlib import crc32

import pytest
from PIL import Image

from ebl.media.domain import ThumbnailSize
from ebl.media.infrastructure import upload_images
from ebl.media.infrastructure.upload_images import (
    UploadValidationError,
    prepare_upload,
)
from ebl.tests.media.upload_image_fixtures import image_bytes


@pytest.mark.parametrize(
    "format,mime",
    [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")],
)
def test_preserves_original_and_generates_all_derivatives(
    format: str, mime: str
) -> None:
    original = image_bytes(format, (1440, 720))
    with prepare_upload(
        BytesIO(original), content_length=len(original), declared_mime_type=mime
    ) as prepared:
        assert prepared.original.content.read() == original
        original_checksum = prepared.original.representation.checksum
        assert original_checksum is not None
        assert original_checksum.value == hashlib.sha256(original).hexdigest()
        assert prepared.original.representation.mime_type == mime
        assert prepared.original.representation.width == 1440
        assert prepared.display.representation.width == 1440
        assert [
            (size, item.representation.width, item.representation.height)
            for size, item in prepared.thumbnails
        ] == [
            (ThumbnailSize.SMALL, 240, 120),
            (ThumbnailSize.MEDIUM, 480, 240),
            (ThumbnailSize.LARGE, 720, 360),
        ]
        streams = [prepared.original.content, prepared.display.content] + [
            item.content for _, item in prepared.thumbnails
        ]
        for item in [prepared.display] + [item for _, item in prepared.thumbnails]:
            content = item.content.read()
            assert item.representation.mime_type == "image/jpeg"
            derivative_checksum = item.representation.checksum
            assert derivative_checksum is not None
            assert hashlib.sha256(content).hexdigest() == derivative_checksum.value
            with Image.open(BytesIO(content)) as decoded:
                decoded.load()
                assert decoded.size == (
                    item.representation.width,
                    item.representation.height,
                )
    assert all(stream.closed for stream in streams)


def test_exif_orientation_changes_only_derivatives() -> None:
    output = BytesIO()
    with Image.new("RGB", (80, 40), "red") as image:
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "Original photographer evidence"
        image.save(output, format="JPEG", exif=exif)
    original = output.getvalue()
    with prepare_upload(BytesIO(original)) as prepared:
        assert prepared.original.content.read() == original
        assert (
            prepared.original.representation.width,
            prepared.original.representation.height,
        ) == (80, 40)
        assert (
            prepared.display.representation.width,
            prepared.display.representation.height,
        ) == (40, 80)
        with Image.open(prepared.original.content) as image:
            assert image.getexif()[315] == "Original photographer evidence"
        with Image.open(prepared.display.content) as image:
            assert image.getexif().get(274, 1) == 1


def test_display_bounded_without_upscaling() -> None:
    with prepare_upload(BytesIO(image_bytes(size=(3000, 1000)))) as prepared:
        assert (
            prepared.display.representation.width,
            prepared.display.representation.height,
        ) == (2560, 853)


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_rejects_truncated_content(format: str) -> None:
    original = image_bytes(format)
    with pytest.raises(UploadValidationError):
        with prepare_upload(BytesIO(original[slice(None, len(original) // 2)])):
            pytest.fail("Truncated image accepted")


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not an image",
        b'<svg xmlns="http://www.w3.org/2000/svg"/>',
        b"GIF89a" + b"\x00" * 100,
    ],
)
def test_rejects_invalid_or_unsupported_content(content: bytes) -> None:
    with pytest.raises(UploadValidationError):
        with prepare_upload(BytesIO(content)):
            pytest.fail("Unsupported image accepted")


def test_rejects_browser_mime_mismatch() -> None:
    with pytest.raises(UploadValidationError, match="Content-Type"):
        with prepare_upload(BytesIO(image_bytes()), declared_mime_type="image/jpeg"):
            pytest.fail("Spoofed type accepted")


def test_rejects_png_with_valid_crc_but_corrupt_compressed_pixels() -> None:
    content = bytearray(image_bytes())
    offset = content.index(b"IDAT")
    length = int.from_bytes(content[slice(offset - 4, offset)], "big")
    content[offset + 4] ^= 255
    checksum_offset = offset + 4 + length
    content[slice(checksum_offset, checksum_offset + 4)] = crc32(
        bytes(content[offset:checksum_offset])
    ).to_bytes(4, "big")
    # Container validation succeeds: full pixel decoding must still reject it.
    with Image.open(BytesIO(bytes(content))) as image:
        image.verify()
    with pytest.raises(UploadValidationError):
        with prepare_upload(BytesIO(bytes(content))):
            pytest.fail("Corrupt compressed pixels accepted")


def sixteen_bit_greyscale_png(width: int, height: int, sample: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc32(body))

    row = b"\x00" + struct.pack(">H", sample) * width
    header = struct.pack(">IIBBBBB", width, height, 16, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(row * height))
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("sample,expected", [(0, 0), (32768, 128), (65535, 255)])
# The wider original also exercises resizing to the display bound.
@pytest.mark.parametrize("width", [200, 3000])
def test_sixteen_bit_greyscale_previews_keep_tone(
    sample: int, expected: int, width: int
) -> None:
    content = BytesIO(sixteen_bit_greyscale_png(width, 40, sample))
    with Image.open(BytesIO(content.getvalue())) as decoded:
        assert decoded.mode == "I;16"
    with prepare_upload(BytesIO(content.getvalue())) as prepared:
        assert prepared.display.representation.width == min(width, 2560)
        for item in [prepared.display] + [item for _, item in prepared.thumbnails]:
            with Image.open(item.content) as preview:
                red, green, blue = cast(
                    Tuple[int, int, int],
                    preview.convert("RGB").getpixel(
                        (preview.width // 2, preview.height // 2)
                    ),
                )
                assert red == green == blue
                assert abs(red - expected) <= 2


ByteOrder = Literal["big", "little"]


def exif_entry_offset(content: bytes, tag: int) -> tuple[int, ByteOrder]:
    tiff = content.index(b"Exif\x00\x00") + 6
    order: ByteOrder = "big" if content[slice(tiff, tiff + 2)] == b"MM" else "little"
    ifd = tiff + int.from_bytes(content[slice(tiff + 4, tiff + 8)], order)
    for index in range(int.from_bytes(content[slice(ifd, ifd + 2)], order)):
        entry = ifd + 2 + 12 * index
        if int.from_bytes(content[slice(entry, entry + 2)], order) == tag:
            return entry, order
    raise AssertionError(f"EXIF tag {tag} not written")


def test_rejects_malformed_exif_as_invalid_content() -> None:
    output = BytesIO()
    with Image.new("RGB", (80, 40), "red") as image:
        exif = Image.Exif()
        exif[274] = 6
        exif[282] = 72.0
        image.save(output, format="JPEG", exif=exif)
    content = bytearray(output.getvalue())
    # Retype XResolution from RATIONAL (5) to ASCII (2): orientation handling
    # then fails re-serialising EXIF with a non-OSError (TypeError).
    entry, order = exif_entry_offset(bytes(content), 282)
    content[slice(entry + 2, entry + 4)] = (2).to_bytes(2, order)
    with pytest.raises(UploadValidationError, match="Invalid or unsafe") as error:
        with prepare_upload(BytesIO(bytes(content))):
            pytest.fail("Malformed EXIF accepted")
    assert error.value.__cause__ is not None


def test_memory_errors_are_not_reported_as_invalid_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exhausted(image: Image.Image) -> Image.Image:
        raise MemoryError()

    monkeypatch.setattr(upload_images.ImageOps, "exif_transpose", exhausted)
    with pytest.raises(MemoryError):
        with prepare_upload(BytesIO(image_bytes())):
            pytest.fail("Exhausted decoder accepted")
