from typing import Sequence

import attr
import pytest

from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.test_corpus_query_route import CHAPTER_WITH_SIGNS_AND_LEMMAS


@pytest.fixture
def exact_chapter_names(text_repository: MongoTextRepository) -> Sequence[str]:
    names = ["I", "I.", "I-", "I_", "I\\0", "I\0", "I\\\0"]
    for name in names:
        text_repository.create_chapter(
            attr.evolve(CHAPTER_WITH_SIGNS_AND_LEMMAS, name=name)
        )
    return names


@pytest.mark.parametrize(
    "query,lines,variants",
    [
        ({"lemmas": ["ina I"]}, (4,), (0,)),
        ({"transliteration": ["TI"]}, (2, 3), (1, 0)),
        ({"lemmas": ["ina I"], "transliteration": ["TI"]}, (2, 3, 4), (1, 0, 0)),
    ],
    ids=["lemma", "sign", "combined"],
)
def test_collation_equivalent_chapters_keep_identity_and_match_metadata(
    text_repository: MongoTextRepository,
    exact_chapter_names: Sequence[str],
    query: dict,
    lines: Sequence[int],
    variants: Sequence[int],
) -> None:
    expected_count = len(exact_chapter_names)
    legacy = text_repository.query(query)
    assert len(legacy.items) == expected_count
    assert {item.name for item in legacy.items} == set(exact_chapter_names)
    assert legacy.match_count_total == expected_count * len(lines)
    names = []

    for offset in range(expected_count + 1):
        result = text_repository.query({**query, "limit": 1, "offset": offset})
        assert result.total_chapters == expected_count
        assert result.match_count_total == expected_count * len(lines)
        assert result.has_next_page == (offset + 1 < expected_count)
        assert len(result.items) == (1 if offset < expected_count else 0)
        for item in result.items:
            names.append(item.name)
            assert item.text_id == CHAPTER_WITH_SIGNS_AND_LEMMAS.text_id
            assert item.stage == CHAPTER_WITH_SIGNS_AND_LEMMAS.stage
            assert item.lines == lines
            assert item.variants == variants
            assert item.match_count == len(lines)

    assert len(names) == len(set(names)) == expected_count
    assert set(names) == set(exact_chapter_names)


def test_browsing_and_matchers_count_the_same_chapter_identities(
    text_repository: MongoTextRepository, exact_chapter_names: Sequence[str]
) -> None:
    browse = text_repository.query({"limit": 100})
    matched = text_repository.query({"lemmas": ["ina I"], "limit": 100})
    assert browse.total_chapters == matched.total_chapters == len(exact_chapter_names)
    assert {item.name for item in browse.items} == {item.name for item in matched.items}
