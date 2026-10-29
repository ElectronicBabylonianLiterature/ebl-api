import re

import pytest

from ebl.sumerian_dictionary.domain.search_query import SumerianWordQuery
from ebl.sumerian_dictionary.domain.sumerian_word import AttingerSense
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_search_pattern import (
    PRECOMPOSED_LATIN_RANGES,
    search_pattern,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_search_ranking import fold
from ebl.tests.factories.sumerian_dictionary import SumerianWordFactory
from ebl.tests.sumerian_dictionary.conftest import InsertWords

DECOMPOSED_CITATION_FORM = "ĝeškim zu"


@pytest.mark.parametrize("query", ["ĝeškim zu", "geskim zu", "geskim"])
def test_combining_marks_in_stored_text_do_not_hide_a_word(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    query: str,
) -> None:
    insert_words(
        SumerianWordFactory.build(
            id="decomposed", citation_form=DECOMPOSED_CITATION_FORM
        )
    )

    result = sumerian_word_repository.search(SumerianWordQuery(query))

    assert [entry.id for entry in result.entries] == ["decomposed"]


@pytest.mark.parametrize("query", ["aiguë", "aigue"])
def test_letters_outside_the_collation_classes_are_found(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    query: str,
) -> None:
    insert_words(
        SumerianWordFactory.build(
            id="accented",
            attinger_senses=(AttingerSense("aiguë", "fr", "att-1"),),
        )
    )

    result = sumerian_word_repository.search(SumerianWordQuery(query))

    assert [entry.id for entry in result.entries] == ["accented"]


def test_every_precomposed_letter_matches_the_pattern_of_its_fold() -> None:
    missed = [
        letter
        for code_range in PRECOMPOSED_LATIN_RANGES
        for letter in map(chr, code_range)
        if len(fold(letter)) == 1
        and not re.fullmatch(search_pattern(fold(letter)), letter, re.IGNORECASE)
    ]

    assert missed == []


def test_braces_and_combining_marks_are_skipped_between_characters() -> None:
    pattern = search_pattern("gesk")

    assert re.search(pattern, "{ĝeš}kim", re.IGNORECASE)
    assert re.search(pattern, "ĝeškim", re.IGNORECASE)
