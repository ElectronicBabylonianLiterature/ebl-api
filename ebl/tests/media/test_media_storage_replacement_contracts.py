from io import BytesIO

import pytest

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredThumbnailRepresentation,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.tests.media.factories import (
    display_representation,
    original_representation,
    photo_media,
    representations,
    thumbnail_representation,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")


def test_stored_representation_handle_rejects_blank_values() -> None:
    for value in ("", " ", "\t", "\n"):
        with pytest.raises(ValueError, match="value"):
            StoredRepresentationHandle(value)


def test_write_returns_distinct_handles_for_the_same_media_role() -> None:
    store = InMemoryRepresentationStore()

    first = store.write_original(_original_write(b"first"))
    second = store.write_original(_original_write(b"second"))

    assert first != second
    assert store.open_representation(first).content.read() == b"first"
    assert store.open_representation(second).content.read() == b"second"


def test_targeted_delete_removes_only_the_selected_handle() -> None:
    store = InMemoryRepresentationStore()
    old_handle = store.write_original(_original_write(b"old"))
    new_handle = store.write_original(_original_write(b"new"))

    store.delete_representation(old_handle)

    assert not store.contains(old_handle)
    assert store.contains(new_handle)
    assert store.open_representation(new_handle).content.read() == b"new"


def test_targeted_delete_of_missing_handle_is_a_noop() -> None:
    store = InMemoryRepresentationStore()

    store.delete_representation(StoredRepresentationHandle("already-gone"))
    store.delete_representation(StoredRepresentationHandle("already-gone"))

    assert store.deleted_handles == [
        StoredRepresentationHandle("already-gone"),
        StoredRepresentationHandle("already-gone"),
    ]


def test_replacement_metadata_failure_leaves_old_metadata_current() -> None:
    store = InMemoryRepresentationStore()
    old = _stored_media(store, "old")
    new = _stored_media(store, "new")
    repository = InMemoryMediaRepository((old,))
    repository.fail_next_replace = True

    with pytest.raises(RuntimeError, match="Metadata replacement failed"):
        repository.replace(new)

    current = repository.find_stored_by_id(PHOTO_ID)
    assert current == old
    assert store.open_representation(old.representations.original).content.read() == (
        b"old-original"
    )
    assert all(store.contains(handle) for handle in new.representations.handles)
    for handle in new.representations.handles:
        store.delete_representation(handle)
    assert all(not store.contains(handle) for handle in new.representations.handles)


def test_cleanup_failure_does_not_roll_back_successful_metadata_switch() -> None:
    store = InMemoryRepresentationStore()
    old = _stored_media(store, "old")
    new = _stored_media(store, "new")
    repository = InMemoryMediaRepository((old,))

    previous = repository.replace(new)
    store.fail_deleting(previous.representations.original)

    with pytest.raises(RuntimeError, match="delete failed"):
        store.delete_representation(previous.representations.original)

    assert repository.find_stored_by_id(PHOTO_ID) == new
    assert store.contains(new.representations.original)
    assert store.contains(previous.representations.original)


def _stored_media(store: InMemoryRepresentationStore, prefix: str) -> StoredMedia:
    media = photo_media(
        media_id_=PHOTO_ID,
        media_representations=representations(display_mime_type="image/jpeg"),
    )
    return StoredMedia(
        media,
        StoredMediaRepresentations(
            store.write_original(_original_write(f"{prefix}-original".encode())),
            (
                StoredThumbnailRepresentation(
                    ThumbnailSize.SMALL,
                    store.write_thumbnail(_thumbnail_write(f"{prefix}-small".encode())),
                ),
            ),
            display=store.write_display(_display_write(f"{prefix}-display".encode())),
        ),
    )


def _original_write(content: bytes) -> OriginalRepresentationWriteRequest:
    return OriginalRepresentationWriteRequest(
        PHOTO_ID, BytesIO(content), original_representation()
    )


def _display_write(content: bytes) -> DisplayRepresentationWriteRequest:
    return DisplayRepresentationWriteRequest(
        PHOTO_ID, BytesIO(content), display_representation()
    )


def _thumbnail_write(content: bytes) -> ThumbnailRepresentationWriteRequest:
    return ThumbnailRepresentationWriteRequest(
        PHOTO_ID,
        BytesIO(content),
        thumbnail_representation(),
        ThumbnailSize.SMALL,
    )
