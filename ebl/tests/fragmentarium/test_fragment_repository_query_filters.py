import pytest

from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
)
from ebl.fragmentarium.domain.fragment import Genre, Script
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import query_summary_of
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize(
    "query,expected",
    [
        ({}, []),
        ({"scriptPeriod": "Hittite"}, [1, 2]),
        ({"scriptPeriod": "Hittite", "scriptPeriodModifier": "Early"}, [1]),
        ({"scriptPeriod": "Neo-Assyrian"}, [3]),
        ({"scriptPeriod": "None"}, [0]),
        ({"scriptPeriod": ""}, [0, 1, 2, 3]),
    ],
)
def test_query_script(fragment_repository, query, expected):
    scripts = [
        Script(),
        Script(Period.HITTITE, PeriodModifier.EARLY),
        Script(Period.HITTITE),
        Script(Period.NEO_ASSYRIAN),
    ]
    fragments = [
        FragmentFactory.build(script=script, number=MuseumNumber.of(f"X.{index}"))
        for index, script in enumerate(scripts)
    ]
    fragment_repository.create_many(fragments)

    assert fragment_repository.query(query) == QueryResult(
        [QueryItem(fragments[index].number, (), 0) for index in expected],
        0,
    )


@pytest.mark.parametrize(
    "query,expected",
    [
        (["MONUMENTAL"], [0]),
        (["ARCHIVAL"], [2]),
        (["CANONICAL"], [1, 2]),
        (["CANONICAL", "Technical"], [1]),
        (["CANONICAL", "Divination"], [2]),
        (["CANONICAL", "Divination", "Celestial"], [2]),
        (["MONUMENTAL", "Narrative"], []),
    ],
)
def test_query_genres(fragment_repository, query, expected):
    test_genres = [
        (Genre(["MONUMENTAL"], False),),
        (Genre(["CANONICAL", "Technical"], False),),
        (
            Genre(["CANONICAL", "Divination"], False),
            Genre(["CANONICAL", "Divination", "Celestial"], False),
            Genre(["ARCHIVAL", "Letter"], False),
        ),
    ]
    fragments = [
        FragmentFactory.build(
            genres=genres_, number=MuseumNumber.of(f"X.{index}"), script=Script()
        )
        for index, genres_ in enumerate(test_genres)
    ]
    fragment_repository.create_many(fragments)

    assert fragment_repository.query({"genre": query}) == QueryResult(
        [QueryItem(fragments[index].number, (), 0) for index in expected],
        0,
    )


@pytest.mark.parametrize(
    "query,expected",
    [
        ({"limit": 2}, [0, 1]),
        ({"offset": 0, "limit": 2}, [0, 1]),
        ({"offset": 2, "limit": 2}, [2, 3]),
    ],
)
def test_query_genres_with_pagination(fragment_repository, query, expected):
    genre = Genre(
        ["CANONICAL", "Technical", "Astronomy", "Astronomical Diaries"],
        False,
    )
    fragments = [
        FragmentFactory.build(
            genres=(genre,), number=MuseumNumber.of(f"X.{index}"), script=Script()
        )
        for index in range(5)
    ]
    for index, fragment in enumerate(fragments):
        fragment_repository.create(fragment, sort_key=index)

    assert fragment_repository.query(
        {"genre": list(genre.category), **query}
    ) == FragmentQueryResultSchema().load(
        {
            "items": [query_summary_of(fragments[index]) for index in expected],
            "matchCountTotal": 0,
        }
    )
