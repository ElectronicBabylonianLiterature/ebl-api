from datetime import date, timedelta
from functools import partial

import attr
import pytest

from ebl.common.domain.project import ResearchProject
from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.queries import LATEST_TRANSLITERATION_LINE_LIMIT
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.factories.record import RecordEntryFactory, RecordFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import query_item_of
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize(
    "query,expected",
    [
        ("CAIC", [0]),
        ("aluGeneva", [1]),
        ("AMPS", [2]),
        ("RECC", [3]),
        (None, [0, 1, 2, 3]),
    ],
)
def test_query_project(fragment_repository, query, expected):
    projects = [
        ResearchProject.CAIC,
        ResearchProject.ALU_GENEVA,
        ResearchProject.AMPS,
        ResearchProject.RECC,
    ]
    fragments = [
        FragmentFactory.build(number=MuseumNumber.of(f"X.{index}"), projects=[project])
        for index, project in enumerate(projects)
    ]
    fragment_repository.create_many(fragments)

    assert fragment_repository.query({"project": query}) == QueryResult(
        [QueryItem(fragments[index].number, (), 0) for index in expected],
        0,
    )


def test_query_latest(fragment_repository):
    start_date = date(2023, 5, 1)
    fragments = [
        TransliteratedFragmentFactory.build(
            record=RecordFactory.build(
                entries=(
                    RecordEntryFactory.build(
                        date=str(start_date + timedelta(index)),
                        type=RecordType.TRANSLITERATION,
                    ),
                )
            ),
        )
        for index in range(5)
    ]
    fragment_repository.create_many(fragments)

    assert fragment_repository.query_latest() == QueryResultSchema().load(
        {
            "items": [
                query_item_of(
                    fragment,
                    tuple(range(LATEST_TRANSLITERATION_LINE_LIMIT)),
                    0,
                )
                for fragment in reversed(fragments)
            ],
            "matchCountTotal": 0,
        }
    )


def test_query_latest_skips_restricted_fragments(fragment_repository):
    open_fragment = TransliteratedFragmentFactory.build()
    restricted_fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_CAIC_FRAGMENTS]
    )
    fragment_repository.create_many([open_fragment, restricted_fragment])

    assert fragment_repository.query_latest() == QueryResultSchema().load(
        {
            "items": [
                query_item_of(
                    open_fragment,
                    tuple(range(LATEST_TRANSLITERATION_LINE_LIMIT)),
                    0,
                )
            ],
            "matchCountTotal": 0,
        }
    )


def test_fetch_fragment_signs(fragment_repository):
    fragments = [
        attr.evolve(FragmentFactory.build(), signs=signs)
        for signs in ["foo", "bar", "", "\n\n"]
    ]
    fragment_repository.create_many(fragments)
    expected = [
        {"_id": str(fragment.number), "signs": fragment.signs}
        for fragment in fragments
        if fragment.signs.strip()
    ]
    sort_by_id = partial(sorted, key=lambda fragment: fragment["_id"])

    assert sort_by_id(fragment_repository.fetch_fragment_signs()) == sort_by_id(
        expected
    )
