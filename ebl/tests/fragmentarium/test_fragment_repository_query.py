from itertools import zip_longest
import random

import attr
import pytest

from ebl.common.query.query_result import QueryResult
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
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
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_query_fragmentarium_number(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert fragment_repository.query(
        {"number": str(fragment.number)}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
        }
    )


def test_query_fragmentarium_not_found(fragment_repository):
    assert fragment_repository.query({"number": "K.1"}) == QueryResult.create_empty()


def test_query_aggregation_allows_disk_use(fragment_repository, monkeypatch):
    aggregate_options = {}

    def aggregate(_pipeline, **kwargs):
        aggregate_options.update(kwargs)
        return iter([])

    monkeypatch.setattr(fragment_repository._fragments, "aggregate", aggregate)

    fragment_repository.query({"number": "K.1"})

    assert aggregate_options["allowDiskUse"] is True


def test_query_fragmentarium_reference_id(database, fragment_repository):
    fragment = FragmentFactory.build(references=(ReferenceFactory.build(),))
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))

    assert fragment_repository.query(
        {"bibId": fragment.references[0].id}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
        }
    )


@pytest.mark.parametrize(
    "pages", ["163", "no. 163", "161-163", "163-161pl. 163", "pl. 42 no. 163"]
)
def test_query_fragmentarium_id_and_pages(pages, database, fragment_repository):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))

    assert fragment_repository.query(
        {"bibId": fragment.references[0].id, "pages": "163"}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
        }
    )


@pytest.mark.parametrize("pages", ["1631", "1163", "116311"])
def test_empty_result_query_reference_id_and_pages(
    pages, database, fragment_repository
):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))

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
    string, expected_lines, fragment_repository, sign_repository, signs
):
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
            }
        )
        if expected_lines
        else QueryResult.create_empty()
    )

    assert result == expected


def test_query_fragmentarium_sorting(fragment_repository, sign_repository, signs):
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
        }
    )


def test_query_fragmentarium_limit_summary_missing_hydration_fails_clearly(
    fragment_repository,
):
    with pytest.raises(NotFoundError, match="Fragment summary data"):
        fragment_repository._load_fragment_query_result(
            {
                "items": [
                    {
                        "_id": "missing",
                        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
                        "matchingLines": [],
                        "matchCount": 0,
                    }
                ],
                "matchCountTotal": 0,
            }
        )


def test_query_fragmentarium_limit_summary_hydration_uses_safe_defaults(
    fragment_repository,
):
    result = FragmentQueryResultSchema().load(
        {
            "items": [
                fragment_repository._hydrate_fragment_query_item(
                    {
                        "_id": "K.1",
                        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
                        "matchingLines": [0, 1],
                    },
                    {
                        "K.1": {
                            "museumNumber": {
                                "prefix": "K",
                                "number": "1",
                                "suffix": "",
                            },
                            "text": {"lines": [{"prefix": "1.", "content": []}]},
                        }
                    },
                    (),
                )
            ],
            "matchCountTotal": 0,
        }
    )

    summary = result.items[0]
    assert summary.description == ""
    assert summary.script == Script()
    assert len(summary.matching_line_preview["lines"]) == 1
