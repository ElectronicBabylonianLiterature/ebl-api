from typing import cast

import attr
import pytest

from ebl.media.application import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredThumbnailRepresentation,
)
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.tests.media.factories import (
    SECOND_PHOTO_MEDIA_ID,
    display_representation,
    photo_media,
    representations,
    stored_media,
)
from ebl.tests.media.in_memory_media import InMemoryMediaRepository

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
OTHER_ID = MediaId(SECOND_PHOTO_MEDIA_ID)


def test_stored_state_requires_original_handle() -> None:
    with pytest.raises(TypeError):
        StoredMediaRepresentations(cast(StoredRepresentationHandle, None))


def test_stored_state_allows_optional_display_and_zero_thumbnails() -> None:
    state = StoredMediaRepresentations(StoredRepresentationHandle("original"))

    assert state.display is None
    assert state.thumbnails == ()
    assert state.handles == (StoredRepresentationHandle("original"),)


def test_stored_state_maps_thumbnail_sizes_to_handles() -> None:
    small = StoredRepresentationHandle("small")
    medium = StoredRepresentationHandle("medium")
    large = StoredRepresentationHandle("large")
    state = StoredMediaRepresentations(
        StoredRepresentationHandle("original"),
        (
            StoredThumbnailRepresentation(ThumbnailSize.SMALL, small),
            StoredThumbnailRepresentation(ThumbnailSize.MEDIUM, medium),
            StoredThumbnailRepresentation(ThumbnailSize.LARGE, large),
        ),
        display=StoredRepresentationHandle("display"),
    )

    assert state.thumbnail(ThumbnailSize.SMALL) == small
    assert state.thumbnail(ThumbnailSize.MEDIUM) == medium
    assert state.thumbnail(ThumbnailSize.LARGE) == large
    assert state.handles == (
        StoredRepresentationHandle("original"),
        StoredRepresentationHandle("display"),
        small,
        medium,
        large,
    )


def test_stored_state_rejects_duplicate_thumbnail_sizes() -> None:
    with pytest.raises(ValueError, match="duplicate thumbnail sizes"):
        StoredMediaRepresentations(
            StoredRepresentationHandle("original"),
            (
                StoredThumbnailRepresentation(
                    ThumbnailSize.SMALL, StoredRepresentationHandle("small-1")
                ),
                StoredThumbnailRepresentation(
                    ThumbnailSize.SMALL, StoredRepresentationHandle("small-2")
                ),
            ),
        )


def test_stored_state_rejects_original_display_handle_reuse() -> None:
    handle = StoredRepresentationHandle("same")

    with pytest.raises(ValueError, match="duplicate representation handles"):
        StoredMediaRepresentations(handle, display=handle)


def test_stored_state_rejects_original_thumbnail_handle_reuse() -> None:
    handle = StoredRepresentationHandle("same")

    with pytest.raises(ValueError, match="duplicate representation handles"):
        StoredMediaRepresentations(
            handle,
            (StoredThumbnailRepresentation(ThumbnailSize.SMALL, handle),),
        )


def test_stored_state_rejects_display_thumbnail_handle_reuse() -> None:
    handle = StoredRepresentationHandle("same")

    with pytest.raises(ValueError, match="duplicate representation handles"):
        StoredMediaRepresentations(
            StoredRepresentationHandle("original"),
            (StoredThumbnailRepresentation(ThumbnailSize.SMALL, handle),),
            display=handle,
        )


def test_stored_state_rejects_small_medium_handle_reuse() -> None:
    handle = StoredRepresentationHandle("same")

    with pytest.raises(ValueError, match="duplicate representation handles"):
        StoredMediaRepresentations(
            StoredRepresentationHandle("original"),
            (
                StoredThumbnailRepresentation(ThumbnailSize.SMALL, handle),
                StoredThumbnailRepresentation(ThumbnailSize.MEDIUM, handle),
            ),
        )


def test_stored_state_is_immutable() -> None:
    field = "display"

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        setattr(
            StoredMediaRepresentations(StoredRepresentationHandle("original")),
            field,
            StoredRepresentationHandle("display"),
        )


def test_stored_media_rejects_representation_shape_mismatch() -> None:
    media = photo_media(
        media_id_=PHOTO_ID,
        media_representations=representations(display=display_representation()),
    )

    with pytest.raises(ValueError, match="must match media metadata"):
        StoredMedia(
            media,
            StoredMediaRepresentations(StoredRepresentationHandle("original")),
        )


def test_repository_contract_creates_complete_stored_media() -> None:
    media = photo_media(media_id_=PHOTO_ID)
    stored = stored_media(media)
    repository = InMemoryMediaRepository()

    assert repository.create(stored) == PHOTO_ID
    assert repository.find_stored_by_id(PHOTO_ID) == stored
    assert repository.find_by_id(PHOTO_ID) == media


def test_repository_contract_rejects_duplicate_stored_media_id() -> None:
    media = photo_media(media_id_=PHOTO_ID)
    repository = InMemoryMediaRepository((stored_media(media),))

    with pytest.raises(MediaAlreadyExistsError):
        repository.create(stored_media(media, "duplicate"))


def test_repository_contract_reads_current_role_handles() -> None:
    media = photo_media(media_id_=PHOTO_ID)
    stored = stored_media(media, "current")
    repository = InMemoryMediaRepository((stored,))
    current = repository.find_stored_by_id(PHOTO_ID)

    assert current is not None
    assert current.representations.original == StoredRepresentationHandle(
        "current-original"
    )
    assert current.representations.thumbnail(ThumbnailSize.SMALL) == (
        StoredRepresentationHandle("current-small")
    )
    assert not hasattr(current.media.representations.original, "handle")


def test_repository_contract_replaces_stored_state_and_returns_previous() -> None:
    old = stored_media(photo_media(media_id_=PHOTO_ID), "old")
    new = stored_media(photo_media(media_id_=PHOTO_ID, caption="new"), "new")
    repository = InMemoryMediaRepository((old,))

    previous = repository.replace(new)

    assert previous == old
    assert repository.find_stored_by_id(PHOTO_ID) == new


def test_repository_contract_rejects_replacing_unknown_stored_state() -> None:
    repository = InMemoryMediaRepository()

    with pytest.raises(MediaNotFoundError):
        repository.replace(stored_media(photo_media(media_id_=PHOTO_ID)))


def test_repository_contract_does_not_silently_change_media_id() -> None:
    old = stored_media(photo_media(media_id_=PHOTO_ID), "old")
    unexpected = stored_media(photo_media(media_id_=OTHER_ID), "other")
    repository = InMemoryMediaRepository((old,))

    with pytest.raises(MediaNotFoundError):
        repository.replace(unexpected)

    assert repository.find_stored_by_id(PHOTO_ID) == old
    assert repository.find_stored_by_id(OTHER_ID) is None
