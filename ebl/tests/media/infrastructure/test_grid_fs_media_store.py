from io import BytesIO
from typing import BinaryIO, cast

import attr
import pytest
from bson import ObjectId
from gridfs import GridFS
from pymongo import ReadPreference
from pymongo.database import Database

from ebl.media.application.media_errors import StoredRepresentationMissingError
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.application.media_storage_identity import StoredRepresentationRole
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.legacy_media_handles import LegacyRepresentationAdoption
from ebl.tests.media.factories import media_id
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)


def test_original_roundtrip_and_fresh_versions(
    representation_store: GridFsMediaRepresentationStore,
) -> None:
    content = image_bytes()
    handles = tuple(
        (
            representation_store.write_original(
                OriginalRepresentationWriteRequest(
                    media_id(), BytesIO(content), image_representation()
                )
            )
            for _ in range(2)
        )
    )
    assert handles[0] != handles[1]
    representation_store.delete_representation(handles[0])
    representation_store.delete_representation(handles[0])
    with pytest.raises(StoredRepresentationMissingError):
        representation_store.open_representation(handles[0])
    opened = representation_store.open_representation(handles[1])
    with opened.content:
        assert opened.content.read() == content
    assert opened.media_id == media_id()
    assert opened.length == len(content)
    third = representation_store.write_original(
        OriginalRepresentationWriteRequest(
            media_id(), BytesIO(content), image_representation()
        )
    )
    assert third not in handles


def test_preview_roles(representation_store: GridFsMediaRepresentationStore) -> None:
    representation = image_representation()
    display = representation_store.write_display(
        DisplayRepresentationWriteRequest(
            media_id(), BytesIO(image_bytes()), representation
        )
    )
    thumbnail = representation_store.write_thumbnail(
        ThumbnailRepresentationWriteRequest(
            media_id(), BytesIO(image_bytes()), representation, ThumbnailSize.MEDIUM
        )
    )
    assert display.role is StoredRepresentationRole.DISPLAY
    assert thumbnail.thumbnail_size is ThumbnailSize.MEDIUM
    with representation_store.open_representation(thumbnail).content as opened:
        assert opened.read() == image_bytes()


def test_storage_overrides_secondary_read_preference(media_database: Database) -> None:
    database = media_database.with_options(read_preference=ReadPreference.SECONDARY)
    store = GridFsMediaRepresentationStore(database)
    handle = store.write_original(
        OriginalRepresentationWriteRequest(
            media_id(), BytesIO(image_bytes()), image_representation()
        )
    )
    with store.open_representation(handle).content as opened:
        assert opened.read() == image_bytes()


def test_forged_handle_cannot_open_or_delete(
    representation_store: GridFsMediaRepresentationStore,
) -> None:
    original = representation_store.write_original(
        OriginalRepresentationWriteRequest(
            media_id(), BytesIO(image_bytes()), image_representation()
        )
    )
    for forged in (
        attr.evolve(original, media_id=MediaId.create()),
        attr.evolve(original, role=StoredRepresentationRole.DISPLAY),
        attr.evolve(
            original, representation=attr.evolve(original.representation, width=9)
        ),
        attr.evolve(original, value="missing"),
    ):
        with pytest.raises(StoredRepresentationMissingError):
            representation_store.open_representation(forged)
        representation_store.delete_representation(forged)
    with representation_store.open_representation(original).content as opened:
        assert opened.read() == image_bytes()


@pytest.mark.parametrize(
    "change",
    [
        {"bucket": "photos"},
        {"ownership": "borrowed"},
        {"ownership": "unknown"},
        {"uploadDate": None},
        {"ready": False},
        {"fileId": "absent"},
    ],
)
def test_invalid_registry_is_not_readable(
    representation_store: GridFsMediaRepresentationStore,
    media_database: Database,
    change: dict,
) -> None:
    handle = representation_store.write_original(
        OriginalRepresentationWriteRequest(
            media_id(), BytesIO(image_bytes()), image_representation()
        )
    )
    media_database.mediaFiles.update_one({"_id": handle.value}, {"$set": change})
    with pytest.raises(StoredRepresentationMissingError):
        representation_store.open_representation(handle)


@pytest.mark.parametrize("ownership", ["owned", "unknown"])
def test_invalid_ownership_cannot_delete_legacy_bytes(
    representation_store: GridFsMediaRepresentationStore,
    media_database: Database,
    ownership: str,
) -> None:
    file_id = GridFS(media_database, "photos").put(image_bytes())
    handle = representation_store.adopt_legacy(
        LegacyRepresentationAdoption(
            media_id(), "photos", file_id, image_representation()
        )
    )
    media_database.mediaFiles.update_one(
        {"_id": handle.value}, {"$set": {"ownership": ownership}}
    )
    with pytest.raises(StoredRepresentationMissingError):
        representation_store.delete_representation(handle)
    assert GridFS(media_database, "photos").get(file_id).read() == image_bytes()


@pytest.mark.parametrize("failure_stage", ["chunks", "file"])
def test_write_failure_cleans_owned_file(
    representation_store: GridFsMediaRepresentationStore,
    media_database: Database,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    original_put = GridFS.put
    retained_id = GridFS(media_database, "media").put(b"unrelated content")

    def fail_upload(
        bucket: GridFS, data: BinaryIO, *, _id: ObjectId, metadata: dict
    ) -> None:
        if failure_stage == "file":
            original_put(bucket, data, _id=_id, metadata=metadata)
        else:
            media_database["media.chunks"].insert_one(
                {"files_id": _id, "n": 0, "data": b"partial upload"}
            )
        assert media_database["media.chunks"].count_documents({"files_id": _id}) > 0
        raise RuntimeError("upload interrupted")

    monkeypatch.setattr(GridFS, "put", fail_upload)
    with pytest.raises(RuntimeError, match="interrupted"):
        representation_store.write_original(
            OriginalRepresentationWriteRequest(
                media_id(), BytesIO(image_bytes()), image_representation()
            )
        )
    assert media_database["media.files"].count_documents({}) == 1
    assert media_database["media.chunks"].count_documents({}) == 1
    assert (
        GridFS(media_database, "media").get(retained_id).read() == b"unrelated content"
    )
    assert (
        media_database.mediaFiles.count_documents({"deleted": True, "ready": False})
        == 1
    )


@pytest.mark.parametrize("limit", [0, -1, True, "large"])
def test_invalid_upload_limit(media_database: Database, limit: object) -> None:
    with pytest.raises(ValueError, match="positive"):
        GridFsMediaRepresentationStore(media_database, max_file_size=cast(int, limit))
