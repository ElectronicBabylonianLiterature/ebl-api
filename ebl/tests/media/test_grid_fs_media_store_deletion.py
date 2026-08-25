import pytest
from pymongo.database import Database

from ebl.errors import Defect
from ebl.media.application import StoredRepresentationMissingError
from ebl.media.infrastructure.grid_fs_media_store import (
    BUCKET,
    GridFsMediaRepresentationStore,
)
from ebl.tests.media.grid_fs_fixtures import (
    DISPLAY_BYTES,
    MEDIA_ID,
    OTHER_MEDIA_ID,
    UNKNOWN_HANDLE,
    UNPARSABLE_HANDLE,
    object_id_of,
    read_representation,
    store,
    write_display,
    write_original,
    write_thumbnail,
)

__all__ = ["store"]


def test_deleting_one_handle_keeps_the_others(
    store: GridFsMediaRepresentationStore,
) -> None:
    original = write_original(store)
    display = write_display(store)
    store.delete_representation(original)

    assert read_representation(store, display) == DISPLAY_BYTES


def test_delete_representation_is_idempotent(
    store: GridFsMediaRepresentationStore,
) -> None:
    handle = write_original(store)
    store.delete_representation(handle)
    store.delete_representation(handle)

    with pytest.raises(StoredRepresentationMissingError):
        store.open_representation(handle)


def test_delete_representation_ignores_an_unparsable_handle(
    store: GridFsMediaRepresentationStore,
) -> None:
    store.delete_representation(UNPARSABLE_HANDLE)


def test_deletes_every_representation_of_one_media(
    store: GridFsMediaRepresentationStore,
) -> None:
    handles = (write_original(store), write_thumbnail(store), write_display(store))
    store.delete_representations(MEDIA_ID)

    for handle in handles:
        with pytest.raises(StoredRepresentationMissingError):
            store.open_representation(handle)


def test_deleting_one_media_never_touches_another(
    store: GridFsMediaRepresentationStore,
) -> None:
    mine = write_original(store, MEDIA_ID, b"mine")
    theirs = write_original(store, OTHER_MEDIA_ID, b"theirs")
    store.delete_representations(MEDIA_ID)

    with pytest.raises(StoredRepresentationMissingError):
        store.open_representation(mine)
    assert read_representation(store, theirs) == b"theirs"


def test_delete_representations_is_idempotent(
    store: GridFsMediaRepresentationStore,
) -> None:
    store.delete_representations(MEDIA_ID)
    store.delete_representations(MEDIA_ID)


def test_open_rejects_an_unknown_handle(
    store: GridFsMediaRepresentationStore,
) -> None:
    with pytest.raises(StoredRepresentationMissingError):
        store.open_representation(UNKNOWN_HANDLE)


def test_open_rejects_an_unparsable_handle(
    store: GridFsMediaRepresentationStore,
) -> None:
    with pytest.raises(StoredRepresentationMissingError):
        store.open_representation(UNPARSABLE_HANDLE)


def test_the_missing_handle_error_never_names_the_handle(
    store: GridFsMediaRepresentationStore,
) -> None:
    with pytest.raises(StoredRepresentationMissingError) as error:
        store.open_representation(UNKNOWN_HANDLE)

    assert UNKNOWN_HANDLE.value not in str(error.value)
    assert error.value.handle == UNKNOWN_HANDLE


def test_open_rejects_inconsistent_stored_metadata(
    store: GridFsMediaRepresentationStore, database: Database
) -> None:
    handle = write_original(store)
    database[f"{BUCKET}.files"].update_one(
        {"_id": object_id_of(handle)}, {"$unset": {"metadata.width": ""}}
    )

    with pytest.raises(Defect):
        store.open_representation(handle)


def test_open_rejects_absent_stored_metadata(
    store: GridFsMediaRepresentationStore, database: Database
) -> None:
    handle = write_original(store)
    database[f"{BUCKET}.files"].update_one(
        {"_id": object_id_of(handle)}, {"$unset": {"metadata": ""}}
    )

    with pytest.raises(Defect):
        store.open_representation(handle)


def test_open_rejects_an_empty_stored_representation(
    store: GridFsMediaRepresentationStore, database: Database
) -> None:
    handle = write_original(store)
    database[f"{BUCKET}.files"].update_one(
        {"_id": object_id_of(handle)}, {"$set": {"length": 0}}
    )

    with pytest.raises(Defect):
        store.open_representation(handle)


def test_creates_the_media_id_index(
    store: GridFsMediaRepresentationStore, database: Database
) -> None:
    store.create_indexes()
    keys = {
        tuple(index["key"])
        for index in database[f"{BUCKET}.files"].index_information().values()
    }

    assert (("metadata.mediaId", 1),) in keys
