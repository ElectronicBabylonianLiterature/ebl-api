import pytest
import re

from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MAX_CANDIDATES,
    NON_STRING_QUERY_MESSAGE,
    MongoAfoRegisterRepository,
    candidate_splits,
)
from ebl.errors import DataError


def build_queries_exceeding_candidate_limit() -> list:
    tokens_per_query = 24
    candidates_per_query = tokens_per_query - 1
    query_count = MAX_CANDIDATES // candidates_per_query + 1
    return [
        " ".join([f"text{index}"] + [f"token{position}" for position in range(23)])
        for index in range(query_count)
    ]


def test_candidate_splits_returns_every_split():
    assert candidate_splits(" A B C ") == [("A", "B C"), ("A B", "C")]


def test_candidate_splits_without_split_point():
    assert candidate_splits("OrNS") == []


def test_candidate_splits_rejects_non_string():
    with pytest.raises(DataError, match=re.escape(NON_STRING_QUERY_MESSAGE)):
        candidate_splits(None)


def test_build_candidate_query_deduplicates_candidates(
    afo_register_repository: MongoAfoRegisterRepository,
):
    assert afo_register_repository._build_candidate_query(["A B", "A B"]) == {
        "$or": [{"text": "A", "textNumber": "B"}]
    }


def test_build_candidate_query_without_candidates(
    afo_register_repository: MongoAfoRegisterRepository,
):
    assert afo_register_repository._build_candidate_query(["OrNS", ""]) is None


def test_build_candidate_query_within_candidate_limit(
    afo_register_repository: MongoAfoRegisterRepository,
):
    queries = build_queries_exceeding_candidate_limit()[:-1]
    candidate_query = afo_register_repository._build_candidate_query(queries)

    assert candidate_query is not None
    assert len(candidate_query["$or"]) <= MAX_CANDIDATES


def test_build_candidate_query_rejects_too_many_candidates(
    afo_register_repository: MongoAfoRegisterRepository,
):
    with pytest.raises(DataError):
        afo_register_repository._build_candidate_query(
            build_queries_exceeding_candidate_limit()
        )


def test_search_by_texts_and_numbers_rejects_too_many_candidates(
    afo_register_repository: MongoAfoRegisterRepository,
):
    with pytest.raises(DataError):
        afo_register_repository.search_by_texts_and_numbers(
            build_queries_exceeding_candidate_limit()
        )
