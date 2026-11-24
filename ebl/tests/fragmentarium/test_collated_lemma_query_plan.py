from typing import Any, List

import pytest
from pymongo.database import Database

from ebl.common.query.query_result import LemmaQueryType
from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    FRAGMENT_LEMMA_COLLATED_INDEX_NAME,
    MongoFragmentRepository,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get import (
    FRAGMENT_QUERY_COLLATION,
)
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION
from ebl.transliteration.domain.museum_number import MuseumNumber

LEMMA_FIELD = "text.lines.content.uniqueLemma"


def test_explicit_collated_lemma_index_coexists_with_simple_index(
    database: Database, fragment_repository: MongoFragmentRepository
) -> None:
    fragment_repository.create_indexes()
    assert (
        FRAGMENT_LEMMA_COLLATED_INDEX_NAME
        not in database[COLLECTION].index_information()
    )

    name = fragment_repository.create_collated_lemma_index()
    indexes = database[COLLECTION].index_information()

    assert name == FRAGMENT_LEMMA_COLLATED_INDEX_NAME
    assert indexes[name]["key"] == [(LEMMA_FIELD, 1)]
    for option, value in FRAGMENT_QUERY_COLLATION.document.items():
        assert indexes[name]["collation"][option] == value
    assert any(
        index["key"] == [(LEMMA_FIELD, 1)] and "collation" not in index
        for index_name, index in indexes.items()
        if index_name != name
    )
    assert fragment_repository.create_collated_lemma_index() == name


def _find_collated_lemma_index_scans(value: Any) -> List[dict]:
    if isinstance(value, dict):
        own = (
            [value]
            if value.get("stage") == "IXSCAN"
            and value.get("indexName") == FRAGMENT_LEMMA_COLLATED_INDEX_NAME
            else []
        )
        return own + [
            stage
            for item in value.values()
            for stage in _find_collated_lemma_index_scans(item)
        ]
    if isinstance(value, list):
        return [
            stage for item in value for stage in _find_collated_lemma_index_scans(item)
        ]
    return []


def _is_point_interval(interval: str) -> bool:
    if not (interval.startswith("[") and interval.endswith("]")):
        return False
    bounds = interval[1:-1].split(", ")
    return len(bounds) == 2 and bounds[0] == bounds[1]


@pytest.mark.parametrize(
    "operator",
    [
        LemmaQueryType.AND,
        LemmaQueryType.OR,
        LemmaQueryType.LINE,
        LemmaQueryType.PHRASE,
    ],
)
def test_collated_lemma_index_bounds_the_search_lemma_predicate(
    database: Database,
    fragment_repository: MongoFragmentRepository,
    operator: LemmaQueryType,
) -> None:
    lemmas = ["ana I", "kīdu I"]
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of("K.1")), sort_key=0
    )
    fragment_repository.create_collated_lemma_index()
    pipeline = PatternMatcher(
        {
            "lemmas": lemmas,
            "lemmaOperator": operator,
            "limit": 10,
            "count": "exact",
        },
        fragment_repository._provenance_service,
    ).build_pipeline()

    plan = database.command(
        "explain",
        {
            "aggregate": COLLECTION,
            "pipeline": pipeline,
            "cursor": {},
            "collation": FRAGMENT_QUERY_COLLATION.document,
            "hint": FRAGMENT_LEMMA_COLLATED_INDEX_NAME,
        },
        verbosity="queryPlanner",
    )

    index_scans = _find_collated_lemma_index_scans(plan)
    assert index_scans
    for index_scan in index_scans:
        intervals = index_scan["indexBounds"][LEMMA_FIELD]
        assert intervals
        assert len(intervals) <= len(lemmas)
        assert all(_is_point_interval(interval) for interval in intervals)
        assert not any("MinKey" in interval for interval in intervals)


@pytest.mark.parametrize(
    "lemma,is_match",
    [
        ("ana I", True),
        ("ana  I", True),
        ("anaI", True),
        ("ana-I", True),
        ("ANA I", False),
    ],
)
@pytest.mark.parametrize("operator", [LemmaQueryType.AND, LemmaQueryType.OR])
def test_collated_lemma_index_preserves_results_for_lemma_variants(
    fragment_repository: MongoFragmentRepository,
    lemma: str,
    is_match: bool,
    operator: LemmaQueryType,
) -> None:
    number = MuseumNumber.of("K.1")
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=number), sort_key=0
    )
    query = {"lemmaOperator": operator, "lemmas": (lemma,)}
    page_query = {**query, "limit": 1, "count": "exact"}
    before = fragment_repository.query(query)
    page_before = fragment_repository.query(page_query)

    assert [item.museum_number for item in before.items] == (
        [number] if is_match else []
    )
    fragment_repository.create_collated_lemma_index()

    assert fragment_repository.query(query) == before
    assert fragment_repository.query(page_query) == page_before
