from io import BytesIO
from typing import Mapping, Sequence

import attr
import pytest

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
)
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.tests.media.factories import display_representation, original_representation
from ebl.tests.media.in_memory_media import InMemoryRepresentationStore

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")


@attr.s(auto_attribs=True, frozen=True)
class StoredRepresentationMetadata:
    original: StoredRepresentationHandle
    display: StoredRepresentationHandle | None = None
    thumbnails: Mapping[ThumbnailSize, StoredRepresentationHandle] = attr.Factory(dict)

    @property
    def handles(self) -> Sequence[StoredRepresentationHandle]:
        handles = [self.original]
        if self.display is not None:
            handles.append(self.display)
        handles.extend(self.thumbnails.values())
        return tuple(handles)


class InMemoryStoredRepresentationMetadataStore:
    def __init__(self, metadata: StoredRepresentationMetadata) -> None:
        self.current = metadata
        self.fail_next_replace = False

    def replace(self, metadata: StoredRepresentationMetadata) -> None:
        if self.fail_next_replace:
            self.fail_next_replace = False
            raise RuntimeError("Metadata replacement failed.")
        self.current = metadata


def test_stored_representation_handle_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="value"):
        StoredRepresentationHandle("")


def test_write_returns_distinct_handles_for_the_same_media_role() -> None:
    store = InMemoryRepresentationStore()

    first = store.write_original(_original_write())
    second = store.write_original(_original_write())

    assert first != second
    assert store.open_representation(first).content.read() == b"media-bytes"
    assert store.open_representation(second).content.read() == b"media-bytes"


def test_targeted_delete_removes_only_the_selected_handle() -> None:
    store = InMemoryRepresentationStore()
    old_handle = store.write_original(_original_write())
    new_handle = store.write_original(_original_write())

    store.delete_representation(old_handle)

    assert not store.contains(old_handle)
    assert store.contains(new_handle)
    assert store.open_representation(new_handle).media_id == PHOTO_ID


def test_targeted_delete_of_missing_handle_is_a_noop() -> None:
    store = InMemoryRepresentationStore()

    store.delete_representation(StoredRepresentationHandle("already-gone"))

    assert store.deleted_handles == [StoredRepresentationHandle("already-gone")]


def test_replacement_metadata_failure_leaves_old_metadata_current() -> None:
    store = InMemoryRepresentationStore()
    old_metadata = StoredRepresentationMetadata(store.write_original(_original_write()))
    metadata_store = InMemoryStoredRepresentationMetadataStore(old_metadata)
    metadata_store.fail_next_replace = True
    new_original = store.write_original(_original_write())
    new_display = store.write_display(_display_write())
    replacement = StoredRepresentationMetadata(new_original, display=new_display)

    with pytest.raises(RuntimeError, match="Metadata replacement failed"):
        metadata_store.replace(replacement)

    assert metadata_store.current == old_metadata
    assert all(store.contains(handle) for handle in replacement.handles)
    for handle in replacement.handles:
        store.delete_representation(handle)
    assert all(not store.contains(handle) for handle in replacement.handles)


def test_cleanup_failure_does_not_roll_back_successful_metadata_switch() -> None:
    store = InMemoryRepresentationStore()
    old_handle = store.write_original(_original_write())
    old_metadata = StoredRepresentationMetadata(old_handle)
    metadata_store = InMemoryStoredRepresentationMetadataStore(old_metadata)
    new_handle = store.write_original(_original_write())
    replacement = StoredRepresentationMetadata(new_handle)

    metadata_store.replace(replacement)
    store.fail_deleting(old_handle)

    with pytest.raises(RuntimeError, match="delete failed"):
        store.delete_representation(old_handle)

    assert metadata_store.current == replacement
    assert store.contains(new_handle)
    assert store.contains(old_handle)


def _original_write() -> OriginalRepresentationWriteRequest:
    return OriginalRepresentationWriteRequest(
        PHOTO_ID, BytesIO(b"media-bytes"), original_representation()
    )


def _display_write() -> DisplayRepresentationWriteRequest:
    return DisplayRepresentationWriteRequest(
        PHOTO_ID, BytesIO(b"media-bytes"), display_representation()
    )
