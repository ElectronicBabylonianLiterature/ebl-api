from typing import Sequence, cast

import pytest
from bson import ObjectId
from pymongo.database import Database

from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.fragment import Genre, Script
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION, SCHEMA
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def identity_fragments(fragment_repository: MongoFragmentRepository) -> Sequence[str]:
    numbers = [
        "X.1",
        "X.01",
        "X.001",
        "X.1.-",
        "X.1._",
        "$X.1",
        "X.é",
        "X.e",
        "X.\\0",
        "X.\0",
        "X.\\\0",
        *(f"X.{index}" for index in range(2, 30)),
    ]
    fragment_repository.create_many(
        [
            LemmatizedFragmentFactory.build(
                number=MuseumNumber.of(number),
                script=Script(Period.NEO_ASSYRIAN),
                genres=(Genre(["CANONICAL"], False),),
            )
            for number in numbers
        ]
    )
    return numbers


@pytest.mark.parametrize(
    "query",
    [
        {"genre": ["CANONICAL"]},
        {"lemmas": ["ana I"]},
        {"transliteration": ["MI"]},
        {"lemmas": ["ana I"], "transliteration": ["MI"]},
    ],
    ids=["metadata", "lemma", "sign", "combined"],
)
def test_matching_documents_keep_exact_museum_number_identity(
    fragment_repository: MongoFragmentRepository,
    identity_fragments: Sequence[str],
    query: dict,
) -> None:
    result = fragment_repository.query({**query, "limit": 100})

    assert result.total_documents == len(identity_fragments)
    assert len(result.items) == len(identity_fragments)
    assert {str(item.museum_number) for item in result.items} == set(identity_fragments)
    assert (
        all(item.match_count > 0 for item in result.items)
        if "genre" not in query
        else result.match_count_total == 0
    )


def test_count_modes_share_stable_pages_without_optional_sort_keys(
    fragment_repository: MongoFragmentRepository, identity_fragments: Sequence[str]
) -> None:
    query = {"genre": ["CANONICAL"]}
    complete = fragment_repository.query(query)
    all_numbers = [str(item.museum_number) for item in complete.items]
    assert len(all_numbers) == len(identity_fragments)
    assert set(all_numbers) == set(identity_fragments)

    for offset in range(0, len(identity_fragments) + 7, 7):
        page_end = offset + 7
        expected = all_numbers[offset:page_end]
        for count in ["exact", "page", "none"]:
            page = fragment_repository.query(
                {**query, "limit": 7, "offset": offset, "count": count}
            )
            assert [str(item.museum_number) for item in page.items] == expected
            assert page.total_documents == (
                len(identity_fragments) if count == "exact" else None
            )
            assert page.has_next_page == (
                offset + len(expected) < len(identity_fragments)
                if count == "page"
                else None
            )


def test_legacy_object_ids_survive_bounded_hydration(
    database: Database, fragment_repository: MongoFragmentRepository
) -> None:
    identifier = ObjectId()
    fragments = [
        LemmatizedFragmentFactory.build(
            number=MuseumNumber.of(f"Legacy.{index}"),
            genres=(Genre(["CANONICAL"], False),),
        )
        for index in range(2)
    ]
    database[COLLECTION].insert_many(
        [
            {**cast(dict, SCHEMA.dump(fragments[0])), "_id": identifier},
            {**cast(dict, SCHEMA.dump(fragments[1])), "_id": str(identifier)},
        ]
    )

    for query in [
        {"genre": ["CANONICAL"]},
        {"lemmas": ["ana I"]},
        {"transliteration": ["MI"]},
        {"lemmas": ["ana I"], "transliteration": ["MI"]},
    ]:
        for pagination in [{}, {"limit": 2}]:
            result = fragment_repository.query({**query, **pagination})
            assert result.total_documents == 2
            assert {item.museum_number for item in result.items} == {
                fragment.number for fragment in fragments
            }
