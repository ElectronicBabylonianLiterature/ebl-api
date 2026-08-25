from typing import Sequence

import pytest
from pymongo.database import Database

from ebl.media.application import MediaRepository, StoredMedia
from ebl.media.domain import MediaAssociation, MediaId, MediaType
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import contract_media, stored_media
from ebl.tests.media.in_memory_media import InMemoryMediaRepository
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
COPY_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")
MISSING_ID = MediaId("550e8400-e29b-41d4-a716-4466554400ff")
K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")
BM99 = MuseumNumber.of("BM.99")


@pytest.fixture(params=["in-memory", "mongo"])
def repository(request, database: Database) -> MediaRepository:
    if request.param == "in-memory":
        return InMemoryMediaRepository()
    return MongoMediaRepository(database)


def _create(repository: MediaRepository, *media: StoredMedia) -> None:
    for item in media:
        repository.create(item)


def _photo(associations: Sequence[MediaAssociation]) -> StoredMedia:
    return stored_media(
        contract_media(PHOTO_ID, MediaType.PHOTO, associations), "photo"
    )


def _copy(associations: Sequence[MediaAssociation]) -> StoredMedia:
    return stored_media(contract_media(COPY_ID, MediaType.COPY, associations), "copy")


def test_finds_created_media_by_id(repository: MediaRepository) -> None:
    photo = _photo((MediaAssociation(K1, 0, True),))
    _create(repository, photo)

    assert repository.find_by_id(PHOTO_ID) == photo.media


def test_returns_none_for_unknown_id(repository: MediaRepository) -> None:
    assert repository.find_by_id(MISSING_ID) is None
    assert repository.find_stored_by_id(MISSING_ID) is None


def test_stored_state_matches_domain_state(repository: MediaRepository) -> None:
    photo = _photo((MediaAssociation(K1, 0, True),))
    _create(repository, photo)
    stored = repository.find_stored_by_id(PHOTO_ID)

    assert stored == photo
    assert stored is not None
    assert stored.media == repository.find_by_id(PHOTO_ID)


def test_reads_fragment_media_in_canonical_order(repository: MediaRepository) -> None:
    photo = _photo((MediaAssociation(K1, 1, False), MediaAssociation(SM2, 0, True)))
    copy = _copy((MediaAssociation(K1, 0, True),))
    _create(repository, photo, copy)

    assert repository.find_by_fragment(K1) == (copy.media, photo.media)
    assert repository.find_by_fragment(SM2) == (photo.media,)


def test_returns_empty_sequence_for_fragment_without_media(
    repository: MediaRepository,
) -> None:
    assert repository.find_by_fragment(K1) == ()


def test_batch_read_keys_every_requested_fragment(
    repository: MediaRepository,
) -> None:
    photo = _photo((MediaAssociation(K1, 0, True), MediaAssociation(SM2, 0, True)))
    _create(repository, photo)

    result = repository.find_by_fragments((K1, SM2, BM99))

    assert set(result) == {K1, SM2, BM99}
    assert result[K1] == (photo.media,)
    assert result[SM2] == (photo.media,)
    assert result[BM99] == ()


def test_batch_read_deduplicates_requested_fragments(
    repository: MediaRepository,
) -> None:
    photo = _photo((MediaAssociation(K1, 0, True),))
    _create(repository, photo)

    result = repository.find_by_fragments((K1, K1))

    assert list(result) == [K1]
    assert result[K1] == (photo.media,)


def test_batch_read_of_no_fragments_is_empty(repository: MediaRepository) -> None:
    assert repository.find_by_fragments(()) == {}


def test_finds_media_within_its_fragment(repository: MediaRepository) -> None:
    photo = _photo((MediaAssociation(K1, 0, True),))
    _create(repository, photo)

    assert repository.find_in_fragment(PHOTO_ID, K1) == photo.media
    assert repository.find_stored_in_fragment(PHOTO_ID, K1) == photo


def test_rejects_media_belonging_to_another_fragment(
    repository: MediaRepository,
) -> None:
    photo = _photo((MediaAssociation(K1, 0, True),))
    _create(repository, photo)

    assert repository.find_in_fragment(PHOTO_ID, SM2) is None
    assert repository.find_stored_in_fragment(PHOTO_ID, SM2) is None


def test_rejects_unknown_media_within_a_fragment(repository: MediaRepository) -> None:
    _create(repository, _photo((MediaAssociation(K1, 0, True),)))

    assert repository.find_in_fragment(MISSING_ID, K1) is None
    assert repository.find_stored_in_fragment(MISSING_ID, K1) is None


def test_prefers_primary_photo_as_primary_media(repository: MediaRepository) -> None:
    photo = _photo((MediaAssociation(K1, 1, True),))
    copy = _copy((MediaAssociation(K1, 0, True),))
    _create(repository, photo, copy)

    assert repository.find_primary_media(K1) == photo.media
    assert repository.find_primary_photo(K1) == photo.media


def test_falls_back_to_primary_copy_without_a_photo(
    repository: MediaRepository,
) -> None:
    copy = _copy((MediaAssociation(K1, 0, True),))
    _create(repository, copy)

    assert repository.find_primary_media(K1) == copy.media
    assert repository.find_primary_photo(K1) is None


def test_returns_no_primary_without_a_primary_association(
    repository: MediaRepository,
) -> None:
    _create(repository, _photo((MediaAssociation(K1, 0, False),)))

    assert repository.find_primary_media(K1) is None
    assert repository.find_primary_photo(K1) is None
