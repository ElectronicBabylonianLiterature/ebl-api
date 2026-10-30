from typing import Dict, Sequence

import attr
import pytest

from ebl.common.domain.stage import Stage
from ebl.common.query.query_result import CorpusQueryItem
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.test_corpus_query_route import (
    CHAPTER_WITH_LEMMA,
    CHAPTER_WITH_SIGNS_AND_LEMMAS,
)


@pytest.fixture
def paginated_chapters(text_repository: MongoTextRepository) -> Sequence[str]:
    names = ["5", "1", "4", "2", "3"]
    for name in names:
        text_repository.create_chapter(
            attr.evolve(
                CHAPTER_WITH_SIGNS_AND_LEMMAS,
                name=name,
                stage=Stage.STANDARD_BABYLONIAN,
            )
        )
    return sorted(names)


@pytest.mark.parametrize(
    "query",
    [
        {"transliteration": ["TI"]},
        {"lemmas": ["ina I"]},
        {"transliteration": ["TI"], "lemmas": ["ina I"]},
    ],
)
@pytest.mark.parametrize(
    "offset,expected_names",
    [(0, ["1", "2"]), (2, ["3", "4"]), (4, ["5"]), (5, []), (99, [])],
)
def test_exact_pages_preserve_all_matching_metadata(
    text_repository: MongoTextRepository,
    paginated_chapters: Sequence[str],
    query: Dict,
    offset: int,
    expected_names: Sequence[str],
) -> None:
    unbounded = text_repository.query(query)
    expected_by_name: Dict[str, CorpusQueryItem] = {
        item.name: item for item in unbounded.items
    }
    result = text_repository.query({**query, "limit": 2, "offset": offset})
    assert result.total_chapters == 5
    assert result.match_count_total == unbounded.match_count_total
    assert result.is_match_count_total_exact is True
    assert [item.name for item in result.items] == expected_names
    assert result.has_next_page == (offset + len(expected_names) < 5)
    assert result.items == [expected_by_name[name] for name in expected_names]


def test_successive_pages_are_stable_and_have_no_duplicate_chapters(
    text_repository: MongoTextRepository, paginated_chapters: Sequence[str]
) -> None:
    names = [
        item.name
        for offset in [0, 2, 4]
        for item in text_repository.query(
            {"lemmas": ["ina I"], "limit": 2, "offset": offset}
        ).items
    ]
    assert names == paginated_chapters
    assert len(names) == len(set(names))
    assert [
        item.name
        for item in text_repository.query({"lemmas": ["ina I"], "limit": 2}).items
    ] == names[:2]


def test_paginated_empty_search_returns_exact_zeroes(
    text_repository: MongoTextRepository,
) -> None:
    result = text_repository.query({"lemmas": ["missing lemma"], "limit": 2})
    assert result.items == []
    assert result.total_chapters == result.match_count_total == 0
    assert result.has_next_page is False


def test_offset_only_repository_request_is_bounded(
    text_repository: MongoTextRepository, paginated_chapters: Sequence[str]
) -> None:
    result = text_repository.query({"offset": 2})
    assert result.total_chapters == 5
    assert [item.name for item in result.items] == paginated_chapters[2:]
    assert result.match_count_total == 0
    assert result.has_next_page is False


def test_match_count_ranking_precedes_chapter_name(
    text_repository: MongoTextRepository,
) -> None:
    high = attr.evolve(CHAPTER_WITH_LEMMA, name="2")
    low = attr.evolve(CHAPTER_WITH_LEMMA, name="1", lines=CHAPTER_WITH_LEMMA.lines[:1])
    text_repository.create_chapter(low)
    text_repository.create_chapter(high)
    result = text_repository.query({"lemmas": ["qanû I"], "limit": 1})
    assert result.total_chapters == 2
    assert result.match_count_total == 3
    assert result.items[0].name == "2"
    assert result.items[0].match_count == 2
    assert result.has_next_page is True


def test_full_chapter_identity_breaks_same_text_and_name_ties(
    text_repository: MongoTextRepository,
) -> None:
    for stage in [Stage.STANDARD_BABYLONIAN, Stage.OLD_BABYLONIAN]:
        text_repository.create_chapter(
            attr.evolve(CHAPTER_WITH_LEMMA, name="1", stage=stage)
        )
    stages = [
        text_repository.query({"lemmas": ["ina I"], "limit": 1, "offset": offset})
        .items[0]
        .stage
        for offset in range(2)
    ]
    assert stages == [Stage.OLD_BABYLONIAN, Stage.STANDARD_BABYLONIAN]
