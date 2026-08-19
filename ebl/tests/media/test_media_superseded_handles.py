import attr
import pytest

from ebl.media.application import (
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredThumbnailRepresentation,
)
from ebl.media.domain import Media, MediaId, ThumbnailSize
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


def state_with_display(
    original: str, small: str, display: str
) -> StoredMediaRepresentations:
    return attr.evolve(state(original, small), display=handle(display))


def photo_with_small_thumbnail() -> Media:
    return photo_media(media_id_=PHOTO_ID)


def photo_with_display() -> Media:
    return photo_media(
        media_id_=PHOTO_ID,
        media_representations=representations(display_mime_type="image/jpeg"),
    )


def stored(media_: Media, representations_: StoredMediaRepresentations) -> StoredMedia:
    return StoredMedia(media_, representations_)


def test_replacing_every_binary_supersedes_every_previous_handle() -> None:
    media = photo_with_small_thumbnail()
    previous = stored(media, state("old-original", "old-small"))
    replacement = stored(media, state("new-original", "new-small"))

    assert set(previous.superseded_by(replacement)) == {
        handle("old-original"),
        handle("old-small"),
    }


def test_replacing_one_binary_supersedes_only_the_changed_handle() -> None:
    media = photo_with_small_thumbnail()
    previous = stored(media, state("old-original", "shared-small"))
    replacement = stored(media, state("new-original", "shared-small"))

    assert previous.superseded_by(replacement) == (handle("old-original"),)


def test_metadata_only_replacement_supersedes_nothing() -> None:
    media = photo_with_small_thumbnail()
    previous = stored(media, state("original", "small"))
    replacement = stored(media, state("original", "small"))

    assert previous.superseded_by(replacement) == ()


def test_superseded_handles_never_include_a_current_handle() -> None:
    media = photo_with_display()
    previous = stored(
        media, state_with_display("old-original", "kept-small", "old-display")
    )
    replacement = stored(
        media, state_with_display("new-original", "kept-small", "new-display")
    )

    superseded = previous.superseded_by(replacement)

    assert set(superseded).isdisjoint(set(replacement.representations.handles))
    assert handle("kept-small") not in superseded


def test_a_handle_that_migrates_between_roles_is_still_current() -> None:
    media = photo_with_small_thumbnail()
    previous = stored(media, state("old-original", "migrating"))
    replacement = stored(media, state("migrating", "new-small"))

    superseded = previous.superseded_by(replacement)

    assert handle("migrating") not in superseded
    assert superseded == (handle("old-original"),)


def test_representation_state_exposes_no_public_supersession_primitive() -> None:
    representation_state = state("original", "small")

    assert not hasattr(representation_state, "superseded_by")


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
