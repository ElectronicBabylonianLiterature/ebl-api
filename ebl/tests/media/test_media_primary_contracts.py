import pytest

from ebl.media.application import (
    MediaNotFoundError,
    has_photo,
    primary_media_for,
    primary_photo_for,
)
from ebl.media.domain import MediaAssociation, MediaId, MediaType
from ebl.tests.media.factories import contract_media
from ebl.tests.media.in_memory_media import InMemoryMediaRepository
from ebl.tests.media.in_memory_media_service import InMemoryMediaService
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
COPY_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")
SECOND_PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440002")
K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")


def photo(media_id: MediaId, sort_order: int, is_primary: bool):
    return contract_media(
        media_id, MediaType.PHOTO, (MediaAssociation(K1, sort_order, is_primary),)
    )


def copy(media_id: MediaId, sort_order: int, is_primary: bool):
    return contract_media(
        media_id, MediaType.COPY, (MediaAssociation(K1, sort_order, is_primary),)
    )


def test_primary_media_prefers_a_primary_photo_over_a_primary_copy() -> None:
    primary_copy = copy(COPY_ID, 0, True)
    primary_photo = photo(PHOTO_ID, 1, True)

    assert primary_media_for(K1, (primary_copy, primary_photo)) == primary_photo
    assert primary_photo_for(K1, (primary_copy, primary_photo)) == primary_photo


def test_primary_media_falls_back_to_a_primary_copy() -> None:
    primary_copy = copy(COPY_ID, 0, True)
    secondary_photo = photo(PHOTO_ID, 1, False)

    assert primary_media_for(K1, (primary_copy, secondary_photo)) == primary_copy
    assert primary_photo_for(K1, (primary_copy, secondary_photo)) is None


def test_primary_selection_is_none_when_nothing_is_flagged_primary() -> None:
    assert primary_media_for(K1, (photo(PHOTO_ID, 0, False),)) is None
    assert primary_photo_for(K1, (photo(PHOTO_ID, 0, False),)) is None
    assert primary_media_for(K1, ()) is None


def test_conflicting_primaries_resolve_deterministically_by_sort_order() -> None:
    later = photo(SECOND_PHOTO_ID, 5, True)
    earlier = photo(PHOTO_ID, 1, True)

    assert primary_media_for(K1, (later, earlier)) == earlier
    assert primary_media_for(K1, (earlier, later)) == earlier


def test_conflicting_primaries_tie_break_on_media_id() -> None:
    first = photo(PHOTO_ID, 0, True)
    second = photo(SECOND_PHOTO_ID, 0, True)

    assert primary_media_for(K1, (second, first)) == first


def test_has_photo_is_true_for_any_associated_photo() -> None:
    assert has_photo(K1, (photo(PHOTO_ID, 0, False),)) is True
    assert has_photo(K1, (copy(COPY_ID, 0, True),)) is False
    assert has_photo(K1, ()) is False


def test_selection_rejects_media_from_another_fragment() -> None:
    unrelated = contract_media(
        PHOTO_ID, MediaType.PHOTO, (MediaAssociation(SM2, 0, True),)
    )

    with pytest.raises(ValueError):
        primary_media_for(K1, (unrelated,))
    with pytest.raises(ValueError):
        has_photo(K1, (unrelated,))


def test_service_owns_the_single_primary_per_fragment_invariant() -> None:
    repository = InMemoryMediaRepository(
        (photo(PHOTO_ID, 0, True), photo(SECOND_PHOTO_ID, 1, True))
    )
    service = InMemoryMediaService(repository)

    updated = service.set_primary_media(K1, SECOND_PHOTO_ID)

    primary = repository.find_primary_media(K1)
    assert [item.association_for(K1).is_primary for item in updated] == [False, True]
    assert primary is not None
    assert primary.id == SECOND_PHOTO_ID


def test_service_primary_transition_only_affects_the_target_fragment() -> None:
    shared = contract_media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(K1, 0, False), MediaAssociation(SM2, 0, True)),
    )
    repository = InMemoryMediaRepository((shared,))
    service = InMemoryMediaService(repository)

    service.set_primary_media(K1, PHOTO_ID)

    updated = repository.find_by_id(PHOTO_ID)
    assert updated is not None
    assert updated.association_for(K1).is_primary is True
    assert updated.association_for(SM2).is_primary is True


def test_service_rejects_promoting_media_outside_the_fragment() -> None:
    repository = InMemoryMediaRepository((photo(PHOTO_ID, 0, True),))
    service = InMemoryMediaService(repository)

    with pytest.raises(MediaNotFoundError):
        service.set_primary_media(SM2, PHOTO_ID)


def test_repository_primary_reads_match_the_shared_selection_policy() -> None:
    primary_copy = copy(COPY_ID, 0, True)
    primary_photo = photo(PHOTO_ID, 1, True)
    repository = InMemoryMediaRepository((primary_copy, primary_photo))

    assert repository.find_primary_media(K1) == primary_photo
    assert repository.find_primary_photo(K1) == primary_photo
    assert repository.find_primary_photo(SM2) is None
