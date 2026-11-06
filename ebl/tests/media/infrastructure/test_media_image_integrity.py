from io import BytesIO
from typing import NoReturn
from zlib import crc32

import pytest
from PIL import Image
from pymongo.database import Database

from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import ThumbnailSize
from ebl.media.infrastructure import media_binary_validation
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.tests.media.factories import media_id
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)


def test_webp_limit_precedes_image_open(monkeypatch: pytest.MonkeyPatch) -> None:
    content = image_bytes("WEBP")
    monkeypatch.setattr(media_binary_validation, "MAX_RASTER_PIXELS", 47)

    def forbidden_open(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("The decoder must not see an excessive canvas.")

    monkeypatch.setattr(Image, "open", forbidden_open)
    with pytest.raises(ValueError, match="pixel limit"):
        media_binary_validation.verified_content(
            BytesIO(content), image_representation(content, "image/webp"), 10000
        )


def test_webp_exact_pixel_limit_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(media_binary_validation, "MAX_RASTER_PIXELS", 48)
    content = image_bytes("WEBP")
    with media_binary_validation.verified_content(
        BytesIO(content), image_representation(content, "image/webp"), 10000
    ) as verified:
        assert verified.read() == content


@pytest.mark.parametrize("missing_bytes", [2, 10])
def test_truncated_jpeg_never_creates_owned_records(
    media_database: Database,
    representation_store: GridFsMediaRepresentationStore,
    missing_bytes: int,
) -> None:
    content = image_bytes("JPEG")[:-missing_bytes]
    with pytest.raises(OSError):
        representation_store.write_original(
            OriginalRepresentationWriteRequest(
                media_id(),
                BytesIO(content),
                image_representation(content, "image/jpeg"),
            )
        )
    assert media_database.mediaFiles.count_documents({}) == 0
    assert media_database["media.files"].count_documents({}) == 0
    assert media_database["media.chunks"].count_documents({}) == 0


def test_complete_jpeg_roundtrips_owned_storage(
    representation_store: GridFsMediaRepresentationStore,
) -> None:
    content = image_bytes("JPEG")
    handle = representation_store.write_original(
        OriginalRepresentationWriteRequest(
            media_id(), BytesIO(content), image_representation(content, "image/jpeg")
        )
    )
    with representation_store.open_representation(handle).content as stored:
        assert stored.read() == content


def corrupted_png_bytes() -> bytes:
    content = bytearray(image_bytes("PNG"))
    chunk_offset = content.index(b"IDAT")
    chunk_size = int.from_bytes(content[chunk_offset - 4 : chunk_offset], "big")
    content[chunk_offset + 4] ^= 255
    checksum_offset = chunk_offset + 4 + chunk_size
    content[checksum_offset : checksum_offset + 4] = crc32(
        bytes(content[chunk_offset:checksum_offset])
    ).to_bytes(4, "big")
    return bytes(content)


def corrupted_webp_bytes() -> bytes:
    content = bytearray(image_bytes("WEBP")[:-4])
    content[4:8] = (len(content) - 8).to_bytes(4, "little")
    content[16:20] = (len(content) - 20).to_bytes(4, "little")
    return bytes(content)


def animated_webp_bytes() -> bytes:
    with BytesIO() as content:
        with Image.new("RGBA", (8, 6), "red") as image:
            with Image.new("RGBA", (8, 6), "blue") as second_frame:
                image.save(content, "WEBP", save_all=True, append_images=[second_frame])
        return content.getvalue()


def corrupted_second_webp_frame() -> bytes:
    content = bytearray(animated_webp_bytes())
    second_frame_offset = content.rfind(b"ANMF")
    assert second_frame_offset > 0
    content[second_frame_offset + 42] ^= 255
    return bytes(content)


@pytest.mark.parametrize(
    "mime_type,content",
    [
        ("image/png", corrupted_png_bytes()),
        ("image/webp", corrupted_webp_bytes()),
        ("image/webp", corrupted_second_webp_frame()),
    ],
    ids=["corrupt-png", "corrupt-webp", "corrupt-later-webp-frame"],
)
@pytest.mark.parametrize("write_kind", ["original", "display", "thumbnail"])
def test_corrupt_raster_never_creates_owned_files(
    media_database: Database,
    representation_store: GridFsMediaRepresentationStore,
    mime_type: str,
    content: bytes,
    write_kind: str,
) -> None:
    representation = image_representation(content, mime_type)
    with Image.open(BytesIO(content)) as image:
        image.verify()
    with pytest.raises(OSError):
        if write_kind == "original":
            representation_store.write_original(
                OriginalRepresentationWriteRequest(
                    media_id(), BytesIO(content), representation
                )
            )
        elif write_kind == "display":
            representation_store.write_display(
                DisplayRepresentationWriteRequest(
                    media_id(), BytesIO(content), representation
                )
            )
        else:
            representation_store.write_thumbnail(
                ThumbnailRepresentationWriteRequest(
                    media_id(), BytesIO(content), representation, ThumbnailSize.SMALL
                )
            )
    assert media_database.mediaFiles.count_documents({}) == 0
    assert media_database["media.files"].count_documents({}) == 0
    assert media_database["media.chunks"].count_documents({}) == 0


def test_animated_webp_has_bounded_total_decode_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = animated_webp_bytes()
    representation = image_representation(content, "image/webp")
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", None)
    monkeypatch.setattr(media_binary_validation, "MAX_RASTER_PIXELS", 95)
    with pytest.raises(ValueError, match="pixel limit"):
        media_binary_validation.verified_content(
            BytesIO(content), representation, 10000
        )
    monkeypatch.setattr(media_binary_validation, "MAX_RASTER_PIXELS", 96)
    with media_binary_validation.verified_content(
        BytesIO(content), representation, 10000
    ) as verified:
        assert verified.read() == content
