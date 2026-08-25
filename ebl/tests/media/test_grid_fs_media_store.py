import pytest

from ebl.media.infrastructure.grid_fs_media_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.application import StoredRepresentationMissingError
from ebl.tests.media.factories import (
    display_representation,
    original_representation,
    thumbnail_representation,
)
from ebl.tests.media.grid_fs_fixtures import (
    DISPLAY_BYTES,
    MEDIA_ID,
    ORIGINAL_BYTES,
    THUMBNAIL_BYTES,
    read_representation,
    store,
    write_display,
    write_original,
    write_thumbnail,
)

__all__ = ["store"]


def test_writes_and_opens_an_original(store: GridFsMediaRepresentationStore) -> None:
    handle = write_original(store)
    opened = store.open_representation(handle)

    assert opened.media_id == MEDIA_ID
    assert opened.representation == original_representation()
    assert opened.length == len(ORIGINAL_BYTES)
    assert opened.content.read() == ORIGINAL_BYTES
    opened.content.close()


def test_writes_and_opens_a_display(store: GridFsMediaRepresentationStore) -> None:
    opened = store.open_representation(write_display(store))

    assert opened.representation == display_representation()
    assert opened.content.read() == DISPLAY_BYTES
    opened.content.close()


def test_writes_and_opens_a_thumbnail(store: GridFsMediaRepresentationStore) -> None:
    opened = store.open_representation(write_thumbnail(store))

    assert opened.representation == thumbnail_representation()
    assert opened.content.read() == THUMBNAIL_BYTES
    opened.content.close()


def test_mime_type_comes_from_stored_metadata(
    store: GridFsMediaRepresentationStore,
) -> None:
    handle = write_original(store, representation=original_representation("image/png"))
    opened = store.open_representation(handle)

    assert opened.representation.mime_type == "image/png"
    opened.content.close()


def test_content_can_be_read_in_chunks(
    store: GridFsMediaRepresentationStore,
) -> None:
    opened = store.open_representation(write_original(store))
    try:
        assert opened.content.read(8) == ORIGINAL_BYTES[:8]
        assert opened.content.read() == ORIGINAL_BYTES[8:]
    finally:
        opened.content.close()


def test_every_write_creates_a_new_logical_version(
    store: GridFsMediaRepresentationStore,
) -> None:
    first = write_original(store, content=b"first-bytes")
    second = write_original(store, content=b"second-bytes")

    assert first != second
    assert read_representation(store, first) == b"first-bytes"
    assert read_representation(store, second) == b"second-bytes"


def test_a_superseded_handle_stays_readable_until_deleted(
    store: GridFsMediaRepresentationStore,
) -> None:
    previous = write_original(store, content=b"previous-bytes")
    write_original(store, content=b"current-bytes")

    assert read_representation(store, previous) == b"previous-bytes"

    store.delete_representation(previous)

    with pytest.raises(StoredRepresentationMissingError):
        store.open_representation(previous)


def test_each_representation_role_is_independently_addressable(
    store: GridFsMediaRepresentationStore,
) -> None:
    handles = (
        write_original(store),
        write_display(store),
        write_thumbnail(store),
    )

    assert len(set(handles)) == 3
