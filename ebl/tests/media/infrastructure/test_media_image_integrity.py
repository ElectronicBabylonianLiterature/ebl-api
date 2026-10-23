from io import BytesIO
from typing import NoReturn

import pytest
from PIL import Image
from pymongo.database import Database

from ebl.media.application.media_stored import OriginalRepresentationWriteRequest
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
