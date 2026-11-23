"""Verify that lemma search can use the explicitly provisioned collated index.

This tests the index-supported access path with a hint in an isolated MongoDB.
Unhinted plan choice and production speedups require representative DB checks.
"""

import pytest

from ebl.common.query.query_result import LemmaQueryType
from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    FRAGMENT_LEMMA_COLLATED_INDEX_NAME,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get import (
    FRAGMENT_QUERY_COLLATION,
)
from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION


def test_explicit_collated_lemma_index_coexists_with_simple_index(
    database, fragment_repository
):
    fragment_repository.create_indexes()
    assert (
        FRAGMENT_LEMMA_COLLATED_INDEX_NAME
        not in database[COLLECTION].index_information()
    )

    name = fragment_repository.create_collated_lemma_index()
    indexes = database[COLLECTION].index_information()

    assert name == FRAGMENT_LEMMA_COLLATED_INDEX_NAME
    assert indexes[name]["key"] == [("text.lines.content.uniqueLemma", 1)]
    for option, value in FRAGMENT_QUERY_COLLATION.document.items():
        assert indexes[name]["collation"][option] == value
    assert any(
        index["key"] == [("text.lines.content.uniqueLemma", 1)]
        and "collation" not in index
        for index_name, index in indexes.items()
        if index_name != name
    )
    assert fragment_repository.create_collated_lemma_index() == name


def _has_collated_lemma_ixscan(value):
    if isinstance(value, dict):
        if (
            value.get("stage") == "IXSCAN"
            and value.get("indexName") == FRAGMENT_LEMMA_COLLATED_INDEX_NAME
        ):
            return True
        return any(_has_collated_lemma_ixscan(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_collated_lemma_ixscan(item) for item in value)
    return False


@pytest.mark.parametrize(
    "operator",
    [LemmaQueryType.AND, LemmaQueryType.OR, LemmaQueryType.LINE],
)
def test_collated_lemma_index_supports_search_query_planner(
    database, fragment_repository, operator
):
    fragment_repository.create_collated_lemma_index()
    pipeline = PatternMatcher(
        {
            "lemmas": ["ana I", "kīdu I"],
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

    assert _has_collated_lemma_ixscan(plan)
