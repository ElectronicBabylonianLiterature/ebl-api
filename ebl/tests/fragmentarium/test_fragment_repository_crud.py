from typing import Sequence, cast

import pytest
from pymongo.database import Database

from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.domain.fragment import Acquisition, Script
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    JoinFactory,
    LemmatizedFragmentFactory,
)
from ebl.tests.fragmentarium.fragment_repository_test_helpers import (
    COLLECTION,
    JOINS_COLLECTION,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import Labels, ParallelFragment
from ebl.transliteration.domain.text import Text


def test_create(database, fragment_repository):
    fragment = LemmatizedFragmentFactory.build()
    fragment_id = fragment_repository.create(fragment)

    assert fragment_id == str(fragment.number)
    assert database[COLLECTION].find_one(
        {"_id": fragment_id}, projection={"_id": False}
    ) == FragmentSchema(exclude=["joins"]).dump(fragment)


def test_create_many(
    database: Database[dict[str, object]], fragment_repository: MongoFragmentRepository
) -> None:
    fragments = [LemmatizedFragmentFactory.build() for _ in range(2)]
    fragment_ids = fragment_repository.create_many(fragments)

    for fragment in fragments:
        assert str(fragment.number) in fragment_ids
        assert database[COLLECTION].find_one(
            {"_id": str(fragment.number)}, projection={"_id": False}
        ) == FragmentSchema(exclude=["joins"]).dump(fragment)


def test_query_by_museum_number_multiple_acquisitions(database, fragment_repository):
    first = Acquisition(description="First purchase", supplier="Gallery A", date=1920)
    second = Acquisition(description="Second purchase", supplier="Gallery B", date=1930)
    fragment = LemmatizedFragmentFactory.build(acquisitions=(first, second))
    fragment_repository.create(fragment)

    queried_fragment = fragment_repository.query_by_museum_number(fragment.number)

    assert queried_fragment.acquisitions == (first, second)


def test_create_indexes(database, fragment_repository):
    fragment_repository.create_indexes()

    fragment_index_keys = [
        index["key"] for index in database[COLLECTION].index_information().values()
    ]
    join_index_keys = [
        index["key"]
        for index in database[JOINS_COLLECTION].index_information().values()
    ]

    assert [("text.lines.content.uniqueLemma", 1)] in fragment_index_keys
    assert [("dossiers.dossierId", 1)] in fragment_index_keys
    assert [("genres.category", 1)] in fragment_index_keys
    assert [
        ("archaeology.excavationNumber.prefix", 1),
        ("archaeology.excavationNumber.number", 1),
        ("archaeology.excavationNumber.suffix", 1),
    ] in fragment_index_keys
    assert [
        ("fragments.museumNumber.prefix", 1),
        ("fragments.museumNumber.number", 1),
        ("fragments.museumNumber.suffix", 1),
    ] in join_index_keys


def test_create_join(
    database: Database[dict[str, object]], fragment_repository: MongoFragmentRepository
) -> None:
    first_join = JoinFactory.build()
    second_join = JoinFactory.build()
    join_schema = JoinSchema(exclude=["is_in_fragmentarium"])

    fragment_repository.create_join([[first_join], [second_join]])

    assert database[JOINS_COLLECTION].find_one({}, projection={"_id": False}) == {
        "fragments": [
            {
                **cast(dict[str, object], join_schema.dump(first_join)),
                "group": 0,
            },
            {
                **cast(dict[str, object], join_schema.dump(second_join)),
                "group": 1,
            },
        ]
    }


@pytest.mark.parametrize("number", ["IM.123", "IM.*"])
def test_query_by_museum_number(database, fragment_repository, number):
    fragments = {
        museum_number: LemmatizedFragmentFactory.build(
            number=MuseumNumber.of(museum_number)
        )
        for museum_number in ["IM.123", "IM.*"]
    }

    database[COLLECTION].insert_many(
        [
            FragmentSchema(exclude=["joins"]).dump(fragment)
            for fragment in fragments.values()
        ]
    )

    fragment = fragments[number]
    queried_fragment = fragment_repository.query_by_museum_number(fragment.number)

    assert queried_fragment == fragment


@pytest.mark.parametrize(
    "query,expected",
    [
        ("IM.*", ["IM.1"]),
        ("BM.*", ["BM.1", "BM.2", "BM.2.a", "BM.2.b", "BM.3.a"]),
        ("BM.*.*", ["BM.1", "BM.2", "BM.2.a", "BM.2.b", "BM.3.a"]),
        ("BM.*.a", ["BM.2.a", "BM.3.a"]),
        ("*.1", ["BM.1", "IM.1"]),
        ("*.3.*", ["BM.3.a"]),
        ("*.*.b", ["BM.2.b"]),
        ("*.*.*", ["BM.1", "BM.2", "BM.2.a", "BM.2.b", "BM.3.a", "IM.1"]),
        ("*.*", ["BM.1", "BM.2", "BM.2.a", "BM.2.b", "BM.3.a", "IM.1"]),
    ],
)
def test_museum_number_wildcard(
    fragment_repository: MongoFragmentRepository, query: str, expected: Sequence[str]
) -> None:
    all_numbers = ["BM.1", "BM.2", "BM.2.a", "BM.2.b", "BM.3.a", "IM.1"]
    fragments = [
        FragmentFactory.build(number=MuseumNumber.of(number), script=Script())
        for number in all_numbers
    ]

    fragment_repository.create_many(fragments)

    expected_result = QueryResult(
        [
            QueryItem(fragment.number, (), 0)
            for fragment in fragments
            if str(fragment.number) in expected
        ],
        0,
        total_documents=len(expected),
    )

    assert fragment_repository.query({"number": query}) == expected_result


def test_query_by_museum_number_joins(
    database: Database[dict[str, object]], fragment_repository: MongoFragmentRepository
) -> None:
    museum_number = MuseumNumber("X", "1")
    first_join = Join(museum_number, is_in_fragmentarium=True)
    second_join = Join(MuseumNumber("X", "2"), is_in_fragmentarium=False)
    fragment = LemmatizedFragmentFactory.build(
        number=museum_number, joins=Joins(((first_join,), (second_join,)))
    )
    database[COLLECTION].insert_one(
        cast(dict[str, object], FragmentSchema(exclude=["joins"]).dump(fragment))
    )
    join_schema = JoinSchema(exclude=["is_in_fragmentarium"])
    database[JOINS_COLLECTION].insert_one(
        {
            "fragments": [
                {
                    **cast(dict[str, object], join_schema.dump(first_join)),
                    "group": 0,
                },
                {
                    **cast(dict[str, object], join_schema.dump(second_join)),
                    "group": 1,
                },
            ]
        }
    )

    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_query_by_museum_number_references(
    database, fragment_repository, bibliography_repository
):
    reference = ReferenceFactory.build(with_document=True)
    fragment = LemmatizedFragmentFactory.build(references=(reference,))
    database[COLLECTION].insert_one(FragmentSchema(exclude=["joins"]).dump(fragment))
    bibliography_repository.create(reference.document)

    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_query_by_parallel_line_exists(database, fragment_repository):
    parallel_number = MuseumNumber.of("K.1")
    fragment = FragmentFactory.build(
        text=Text(
            (
                ParallelFragment(
                    False, parallel_number, True, Labels(), LineNumber(1), True
                ),
            )
        )
    )
    parallel_fragment = FragmentFactory.build(number=parallel_number)
    database[COLLECTION].insert_many(
        [
            FragmentSchema(exclude=["joins"]).dump(fragment),
            FragmentSchema(exclude=["joins"]).dump(parallel_fragment),
        ]
    )

    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_fragment_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.query_by_museum_number(MuseumNumber("unknown", "id"))
