import hashlib
from io import BytesIO
import pytest
from PIL import Image
from pymongo.database import Database
from ebl.media.application.media_stored import DisplayRepresentationWriteRequest
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.domain import MediaId
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.upload_images import (
    prepare_upload,
)
from ebl.tests.media.in_memory_representation_store import InMemoryRepresentationStore

from ebl.tests.media.upload_image_fixtures import image_bytes


def test_stores_owned_handles_and_journals_each_write() -> None:
    store = InMemoryRepresentationStore()
    journal: list[StoredRepresentationHandle] = []
    original = image_bytes()
    with prepare_upload(BytesIO(original)) as prepared:
        handles = prepared.store(store, MediaId.create(), journal.append)
    assert len(journal) == 5
    assert len({handle.value for handle in journal}) == 5
    with store.open_representation(handles.original).content as content:
        assert content.read() == original


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_real_gridfs_owned_original_and_derivative_roundtrip(
    media_database: Database, format: str
) -> None:
    store = GridFsMediaRepresentationStore(media_database)
    store.create_indexes()
    original = image_bytes(format)
    journal: list[StoredRepresentationHandle] = []
    with prepare_upload(BytesIO(original)) as prepared:
        handles = prepared.store(store, MediaId.create(), journal.append)
    assert media_database["media.files"].count_documents({}) == 5
    assert media_database["photos.files"].count_documents({}) == 0
    assert len(journal) == 5
    with store.open_representation(handles.original).content as content:
        assert content.read() == original
    for handle in handles.handles:
        with store.open_representation(handle).content as content:
            value = content.read()
        stored_checksum = handle.representation.checksum
        assert stored_checksum is not None
        assert hashlib.sha256(value).hexdigest() == stored_checksum.value
        with Image.open(BytesIO(value)) as image:
            image.load()
            assert image.size == (
                handle.representation.width,
                handle.representation.height,
            )


def test_real_gridfs_failed_derivative_cleans_only_uncommitted_upload(
    media_database: Database,
) -> None:
    class FailingStore(GridFsMediaRepresentationStore):
        def write_display(
            self, request: DisplayRepresentationWriteRequest
        ) -> StoredRepresentationHandle:
            raise RuntimeError("interrupted display write")

    healthy = GridFsMediaRepresentationStore(media_database)
    healthy.create_indexes()
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        previous = prepared.store(healthy, MediaId.create())
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="interrupted display write"):
            prepared.store(FailingStore(media_database), MediaId.create())
    assert media_database["media.files"].count_documents({}) == 5
    assert media_database["media.chunks"].count_documents({}) == 5
    assert media_database.mediaFiles.count_documents({"deleted": True}) == 1
    with healthy.open_representation(previous.original).content as content:
        assert content.read() == image_bytes()


def test_failed_store_cleans_only_current_upload_handles() -> None:
    class FailingStore(InMemoryRepresentationStore):
        def write_display(
            self, request: DisplayRepresentationWriteRequest
        ) -> StoredRepresentationHandle:
            raise RuntimeError("storage interrupted")

    store = FailingStore()
    journal: list[StoredRepresentationHandle] = []
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="storage interrupted"):
            prepared.store(store, MediaId.create(), journal.append)
    assert len(journal) == 1
    assert store.deleted_handles == journal
    assert not store.contains(journal[0])


def test_failed_journal_callback_cleans_staged_handle() -> None:
    store = InMemoryRepresentationStore()

    def failure(handle: StoredRepresentationHandle) -> None:
        raise RuntimeError("journal unavailable")

    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="journal unavailable"):
            prepared.store(store, MediaId.create(), failure)
    assert len(store.deleted_handles) == 1


def test_cleanup_failure_keeps_primary_failure_and_registered_orphan(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FailingStore(InMemoryRepresentationStore):
        def write_display(
            self, request: DisplayRepresentationWriteRequest
        ) -> StoredRepresentationHandle:
            raise RuntimeError("storage interrupted")

        def delete_representation(self, handle: StoredRepresentationHandle) -> None:
            raise RuntimeError("cleanup interrupted")

    store = FailingStore()
    journal: list[StoredRepresentationHandle] = []
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="storage interrupted"):
            prepared.store(store, MediaId.create(), journal.append)
    assert store.contains(journal[0])
    assert "Upload staging cleanup failed" in caplog.text
