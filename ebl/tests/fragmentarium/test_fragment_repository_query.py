from typing import cast
from collections.abc import Iterator, Mapping, Sequence
from itertools import zip_longest
import random

import attr
import pytest
from pymongo.database import Database

from ebl.common.query.query_result import QueryResult
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import query_item_of
from ebl.tests.fragmentarium.fragment_repository_test_helpers import (
    COLLECTION,
    SCHEMA,
    create_transliteration_query_lines,
)
from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.fragment import Script
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign import Sign


def test_query_fragmentarium_number(
    database: Database[dict[str, object]],
    fragment_repository: MongoFragmentRepository,
) -> None:
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [
            cast(dict, SCHEMA.dump(fragment)),
            cast(dict, SCHEMA.dump(FragmentFactory.build())),
        ]
    )

    assert fragment_repository.query(
        {"number": str(fragment.number)}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
            "totalDocuments": 1,
        }
    )


def test_query_fragmentarium_not_found(
    fragment_repository: MongoFragmentRepository,
) -> None:
    assert fragment_repository.query({"number": "K.1"}) == QueryResult.create_empty()


def test_query_aggregation_allows_disk_use(
    fragment_repository: MongoFragmentRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    aggregate_options: dict[str, object] = {}

    def aggregate(
        _pipeline: Sequence[Mapping[str, object]], **kwargs: object
    ) -> Iterator[dict[str, object]]:
        aggregate_options.update(kwargs)
        return iter([])

    monkeypatch.setattr(fragment_repository._fragments, "aggregate", aggregate)

    fragment_repository.query({"number": "K.1"})

    assert aggregate_options["allowDiskUse"] is True


def test_query_fragmentarium_reference_id(
    database: Database[dict[str, object]],
    fragment_repository: MongoFragmentRepository,
) -> None:
    fragment = FragmentFactory.build(references=(ReferenceFactory.build(),))
    database[COLLECTION].insert_one(cast(dict, SCHEMA.dump(fragment)))

    assert fragment_repository.query(
        {"bibId": fragment.references[0].id}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
            "totalDocuments": 1,
        }
    )


@pytest.mark.parametrize(
    "pages", ["163", "no. 163", "161-163", "163-161pl. 163", "pl. 42 no. 163"]
)
def test_query_fragmentarium_id_and_pages(
    pages: str,
    database: Database[dict[str, object]],
    fragment_repository: MongoFragmentRepository,
) -> None:
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(cast(dict, SCHEMA.dump(fragment)))

    assert fragment_repository.query(
        {"bibId": fragment.references[0].id, "pages": "163"}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
            "totalDocuments": 1,
        }
    )


@pytest.mark.parametrize("pages", ["1631", "1163", "116311"])
def test_empty_result_query_reference_id_and_pages(
    pages: str,
    database: Database[dict[str, object]],
    fragment_repository: MongoFragmentRepository,
) -> None:
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(cast(dict, SCHEMA.dump(fragment)))

    assert (
        fragment_repository.query({"bibId": fragment.references[0].id, "pages": "163"})
        == QueryResult.create_empty()
    )


@pytest.mark.parametrize(
    "string,expected_lines",
    [
        ("DIŠ UD", [1]),
        ("KU", [0]),
        ("UD", [1, 3]),
        ("MI DIŠ\nU BA MA", [1, 2]),
        ("IGI UD", []),
    ],
)
def test_query_fragmentarium_transliteration(
    string: str,
    expected_lines: list[int],
    fragment_repository: MongoFragmentRepository,
    sign_repository: SignRepository,
    signs: Sequence[Sign],
) -> None:
    for sign in signs:
        sign_repository.create(sign)

    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create_many([transliterated_fragment, FragmentFactory.build()])

    pattern = create_transliteration_query_lines(string, sign_repository)
    result = fragment_repository.query({"transliteration": pattern})
    expected = (
        QueryResultSchema().load(
            {
                "items": [
                    query_item_of(
                        transliterated_fragment,
                        expected_lines,
                        len(expected_lines) - (len(pattern) > 1),
                    )
                ],
                "matchCountTotal": len(expected_lines) - (len(pattern) > 1),
                "totalDocuments": 1,
            }
        )
        if expected_lines
        else QueryResult.create_empty()
    )

    assert result == expected


def test_query_fragmentarium_sorting(
    fragment_repository: MongoFragmentRepository,
    sign_repository: SignRepository,
    signs: Sequence[Sign],
) -> None:
    for sign in signs:
        sign_repository.create(sign)

    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.0"), script=Script(Period.FARA)
        ),
        attr.evolve(
            TransliteratedFragmentFactory.build(
                number=MuseumNumber.of("X.3"), script=Script(Period.OLD_ASSYRIAN)
            ),
            signs="KU\nX\nDU\nKU\nMI",
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.1"), script=Script(Period.HELLENISTIC)
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.2"), script=Script(Period.PROTO_ELAMITE)
        ),
    ]
    lines = [[0], [0, 3], [0], [0]]

    fragment_repository.create_many(random.sample(fragments, len(fragments)))

    result = fragment_repository.query(
        {"transliteration": create_transliteration_query_lines("KU", sign_repository)}
    )

    assert result == QueryResultSchema().load(
        {
            "items": [
                query_item_of(fragment, fragment_lines)
                for fragment, fragment_lines in zip_longest(fragments, lines)
            ],
            "matchCountTotal": 5,
            "totalDocuments": 4,
        }
    )
