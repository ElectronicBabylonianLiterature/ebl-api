from typing import List

import pytest
from pymongo.database import Database

from ebl.common.domain.project import ResearchProject
from ebl.media.domain import (
    MediaAssociation,
    MediaReference,
    MediaRepresentations,
    MediaType,
    ThumbnailSize,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import (
    large_thumbnail_representation,
    representations,
    medium_thumbnail_representation,
    original_representation,
    photo_media,
    stored_media,
    thumbnail_representation,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")
BM99 = MuseumNumber.of("BM.99")


@pytest.fixture
def repository(database: Database) -> MongoMediaRepository:
    return MongoMediaRepository(database)


def _record_queries(
    repository: MongoMediaRepository, monkeypatch: pytest.MonkeyPatch, method: str
) -> List[object]:
    queries: List[object] = []
    original = getattr(repository._collection, method)

    def recording(query: object, *args: object, **kwargs: object) -> object:
        queries.append(query)
        return original(query, *args, **kwargs)

    monkeypatch.setattr(repository._collection, method, recording)
    return queries


def test_batch_read_issues_one_query_for_many_fragments(
    repository: MongoMediaRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository.create(
        stored_media(
            photo_media(
                associations=(
                    MediaAssociation(K1, 0, True),
                    MediaAssociation(SM2, 0, True),
                )
            )
        )
    )
    queries = _record_queries(repository, monkeypatch, "find_many")
    result = repository.find_by_fragments((K1, SM2, BM99))

    assert len(queries) == 1
    assert set(result) == {K1, SM2, BM99}


def test_batch_read_of_no_fragments_issues_no_query(
    repository: MongoMediaRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    queries = _record_queries(repository, monkeypatch, "find_many")

    assert repository.find_by_fragments(()) == {}
    assert queries == []


def test_cross_fragment_lookup_is_filtered_by_the_database(
    repository: MongoMediaRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    stored = stored_media(photo_media())
    repository.create(stored)
    queries = _record_queries(repository, monkeypatch, "find_one")

    assert repository.find_in_fragment(stored.media.id, SM2) is None
    assert queries == [
        {"_id": str(stored.media.id), "associations.fragmentId": str(SM2)}
    ]


def test_stored_cross_fragment_lookup_is_filtered_by_the_database(
    repository: MongoMediaRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    stored = stored_media(photo_media())
    repository.create(stored)
    queries = _record_queries(repository, monkeypatch, "find_one")

    assert repository.find_stored_in_fragment(stored.media.id, SM2) is None
    assert queries == [
        {"_id": str(stored.media.id), "associations.fragmentId": str(SM2)}
    ]


def test_primary_photo_query_filters_by_type_in_the_database(
    repository: MongoMediaRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository.create(stored_media(photo_media()))
    queries = _record_queries(repository, monkeypatch, "find_many")
    repository.find_primary_photo(K1)

    assert queries == [
        {"associations.fragmentId": str(K1), "type": MediaType.PHOTO.value}
    ]


def test_round_trips_projects_and_references(
    repository: MongoMediaRepository,
) -> None:
    stored = stored_media(
        photo_media(
            projects=(ResearchProject.CAIC,),
            references=(MediaReference("bibliography-id"),),
        )
    )
    repository.create(stored)

    assert repository.find_by_id(stored.media.id) == stored.media


def test_round_trips_every_thumbnail_size(repository: MongoMediaRepository) -> None:
    representations = MediaRepresentations(
        original_representation(),
        (
            (ThumbnailSize.SMALL, thumbnail_representation()),
            (ThumbnailSize.MEDIUM, medium_thumbnail_representation()),
            (ThumbnailSize.LARGE, large_thumbnail_representation()),
        ),
    )
    stored = stored_media(photo_media(media_representations=representations))
    repository.create(stored)

    assert repository.find_stored_by_id(stored.media.id) == stored


def test_round_trips_a_display_representation(
    repository: MongoMediaRepository,
) -> None:
    stored = stored_media(
        photo_media(
            media_representations=representations(display_mime_type="image/png")
        )
    )
    repository.create(stored)

    assert repository.find_stored_by_id(stored.media.id) == stored
