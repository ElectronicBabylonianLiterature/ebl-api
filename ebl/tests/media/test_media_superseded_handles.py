import attr
import pytest

from ebl.media.application import (
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredThumbnailRepresentation,
)
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.tests.media.factories import photo_media, representations, stored_media
from ebl.tests.media.in_memory_media import InMemoryMediaRepository

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")


def handle(value: str) -> StoredRepresentationHandle:
    return StoredRepresentationHandle(value)


def state(original: str, small: str) -> StoredMediaRepresentations:
    return StoredMediaRepresentations(
        handle(original),
        (StoredThumbnailRepresentation(ThumbnailSize.SMALL, handle(small)),),
    )


def test_replacing_every_binary_supersedes_every_previous_handle() -> None:
    previous = state("old-original", "old-small")
    replacement = state("new-original", "new-small")

    assert set(previous.superseded_by(replacement)) == {
        handle("old-original"),
        handle("old-small"),
    }


def test_replacing_one_binary_supersedes_only_the_changed_handle() -> None:
    previous = state("old-original", "shared-small")
    replacement = state("new-original", "shared-small")

    assert previous.superseded_by(replacement) == (handle("old-original"),)


def test_metadata_only_replacement_supersedes_nothing() -> None:
    previous = state("original", "small")
    replacement = state("original", "small")

    assert previous.superseded_by(replacement) == ()


def test_superseded_handles_never_include_a_current_handle() -> None:
    previous = StoredMediaRepresentations(
        handle("old-original"),
        (StoredThumbnailRepresentation(ThumbnailSize.SMALL, handle("kept-small")),),
        display=handle("old-display"),
    )
    replacement = StoredMediaRepresentations(
        handle("new-original"),
        (StoredThumbnailRepresentation(ThumbnailSize.SMALL, handle("kept-small")),),
        display=handle("new-display"),
    )

    superseded = previous.superseded_by(replacement)

    assert set(superseded).isdisjoint(set(replacement.handles))
    assert handle("kept-small") not in superseded


def test_stored_media_supersession_delegates_to_representation_state() -> None:
    media = photo_media(media_id_=PHOTO_ID)
    previous = stored_media(media, "old")
    replacement = stored_media(media, "new")

    assert set(previous.superseded_by(replacement)) == set(
        previous.representations.handles
    )
    assert set(previous.superseded_by(replacement)).isdisjoint(
        set(replacement.representations.handles)
    )


def test_primary_metadata_replacement_leaves_no_cleanup_candidates() -> None:
    media = photo_media(media_id_=PHOTO_ID, media_representations=representations())
    previous = stored_media(media, "current")
    repository = InMemoryMediaRepository((previous,))
    renamed = attr.evolve(previous, media=attr.evolve(media, caption="Obverse"))

    returned_previous = repository.replace(renamed)

    assert returned_previous == previous
    assert returned_previous.superseded_by(renamed) == ()


def test_replace_returns_the_previous_state_not_the_replacement() -> None:
    media = photo_media(media_id_=PHOTO_ID)
    previous = stored_media(media, "old")
    replacement = stored_media(media, "new")
    repository = InMemoryMediaRepository((previous,))

    returned = repository.replace(replacement)

    assert returned == previous
    assert returned != replacement
    assert repository.find_stored_by_id(PHOTO_ID) == replacement


def test_store_writes_return_a_handle_distinct_from_the_live_one() -> None:
    media = photo_media(media_id_=PHOTO_ID)
    previous = stored_media(media, "old")
    replacement = stored_media(media, "new")

    assert replacement.representations.original != previous.representations.original
    assert isinstance(replacement, StoredMedia)


def test_supersession_rejects_stored_state_of_a_different_media() -> None:
    other_id = MediaId("550e8400-e29b-41d4-a716-446655440002")
    previous = stored_media(photo_media(media_id_=PHOTO_ID), "old")
    unrelated = stored_media(photo_media(media_id_=other_id), "other")

    with pytest.raises(ValueError, match="different media"):
        previous.superseded_by(unrelated)
