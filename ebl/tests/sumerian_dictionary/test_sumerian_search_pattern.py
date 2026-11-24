import re

import pytest

from ebl.sumerian_dictionary.domain.search_query import SumerianWordQuery
from ebl.sumerian_dictionary.domain.sumerian_word import AttingerSense, Epsd2Sense
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_search_pattern import (
    PRECOMPOSED_LATIN_RANGES,
    search_pattern,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_search_ranking import (
    DIGRAPHS,
    fold,
)
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


def test_every_digraph_matches_the_pattern_of_its_fold() -> None:
    missed = [
        digraph
        for digraph, _ in DIGRAPHS
        if not re.fullmatch(search_pattern(fold(digraph)), digraph, re.IGNORECASE)
    ]

    assert missed == []


@pytest.mark.parametrize("query", ["contest, dispute", "contest dispute"])
def test_stored_comma_after_t_does_not_hide_an_english_sense(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    query: str,
) -> None:
    sense = Epsd2Sense("1.", "contest, dispute, debate", "en")
    insert_words(SumerianWordFactory.build(id="contest", epsd2_senses=(sense,)))

    result = sumerian_word_repository.search(SumerianWordQuery(query))

    assert [entry.id for entry in result.entries] == ["contest"]


@pytest.mark.parametrize("query", ["bras, force", "bras force"])
def test_stored_comma_after_s_does_not_hide_a_french_sense(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    query: str,
) -> None:
    sense = AttingerSense("bras, force, vigueur", "fr", "att-1")
    insert_words(SumerianWordFactory.build(id="arm", attinger_senses=(sense,)))

    result = sumerian_word_repository.search(SumerianWordQuery(query))

    assert [entry.id for entry in result.entries] == ["arm"]


@pytest.mark.parametrize(
    "stored,query",
    [
        ("Ninmunuszid", "Ninmunuszid"),
        ("Ninmunuszid", "ninmunušid"),
        ("tam₂-szi-lum", "tam2-szi-lum"),
        ("t,u", "ṭu"),
        ("s,a", "ṣa"),
    ],
)
def test_ascii_digraphs_in_stored_forms_are_found(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    stored: str,
    query: str,
) -> None:
    insert_words(SumerianWordFactory.build(id="ascii", citation_form=stored))

    result = sumerian_word_repository.search(SumerianWordQuery(query))

    assert [entry.id for entry in result.entries] == ["ascii"]
