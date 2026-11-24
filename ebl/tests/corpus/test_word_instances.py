from typing import List, Sequence

import pytest

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.word_instances import (
    WordInstances,
    WordLemma,
    find_word_instances,
    is_word_instance,
)
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.line_move_support import (
    LEMMA,
    LINE_COUNT,
    OTHER_LEMMA,
    assert_lines_are_annotated,
)
from ebl.tests.corpus.word_instances_reference import (
    find_manuscript_token,
    find_reconstruction_token,
)
from ebl.tests.corpus.word_instances_support import (
    COUNT_CASES,
    INSTANCE_LINES,
    INSTANCES_LINE_COUNT,
    KEPT_LEMMA,
    LEMMATIZED_COUNT,
    MANUSCRIPT_INSTANCES,
    NEW_LEMMA,
    NO_INSTANCE_INDICES,
    NOT_LEMMATIZABLE_MANUSCRIPT,
    NOT_LEMMATIZABLE_RECONSTRUCTION,
    RECONSTRUCTION_INSTANCES,
    WORD,
    WORD_COUNT,
    CountCase,
    create_instances_chapter,
)
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.tokens import Token, ValueToken
from ebl.transliteration.domain.word_tokens import AbstractWord, Word

REVISION = "0123456789abcdef01234567"


@pytest.fixture
def chapter() -> Chapter:
    return create_instances_chapter()


def find_instance_tokens(chapter: Chapter) -> List[Token]:
    return [
        *(
            find_reconstruction_token(chapter, instance)
            for instance in RECONSTRUCTION_INSTANCES
        ),
        *(
            find_manuscript_token(chapter, instance)
            for instance in MANUSCRIPT_INSTANCES
        ),
    ]


def find_identities(tokens: Sequence[Token]) -> List[int]:
    return sorted(id(token) for token in tokens)


def test_lines_of_the_chapter_are_annotated(chapter: Chapter) -> None:
    assert_lines_are_annotated(chapter.lines[:LINE_COUNT])
    assert len(chapter.lines) == INSTANCES_LINE_COUNT
    assert [len(line.variants) for line in chapter.lines[LINE_COUNT:]] == [2, 1]


def test_instances_have_no_lemma_the_new_lemma_and_other_lemmas(
    chapter: Chapter,
) -> None:
    stored_lemmas = [
        token.unique_lemma
        for token in find_instance_tokens(chapter)
        if isinstance(token, AbstractWord)
    ]

    assert stored_lemmas == [
        *(instance.lemma for instance in RECONSTRUCTION_INSTANCES),
        *(instance.lemma for instance in MANUSCRIPT_INSTANCES),
    ]
    assert set(stored_lemmas) == {(), NEW_LEMMA, LEMMA, OTHER_LEMMA}
    assert len(stored_lemmas) == WORD_COUNT
    assert len(list(filter(None, stored_lemmas))) == LEMMATIZED_COUNT


def test_every_instance_is_a_lemmatizable_word_with_the_clean_value(
    chapter: Chapter,
) -> None:
    tokens = find_instance_tokens(chapter)

    assert all(isinstance(token, AbstractWord) for token in tokens)
    assert all(token.lemmatizable for token in tokens)
    assert {token.clean_value for token in tokens} == {WORD}
    assert all(is_word_instance(token, WORD) for token in tokens)


def test_token_with_the_clean_value_that_is_not_a_word_is_not_an_instance(
    chapter: Chapter,
) -> None:
    token = find_reconstruction_token(chapter, NOT_LEMMATIZABLE_RECONSTRUCTION)

    assert isinstance(token, ValueToken)
    assert token.clean_value == WORD
    assert not is_word_instance(token, WORD)


def test_word_with_the_clean_value_that_is_not_lemmatizable_is_not_an_instance(
    chapter: Chapter,
) -> None:
    token = find_manuscript_token(chapter, NOT_LEMMATIZABLE_MANUSCRIPT)

    assert isinstance(token, Word)
    assert token.clean_value == WORD
    assert token.language is Language.HITTITE
    assert not token.lemmatizable
    assert token.unique_lemma == KEPT_LEMMA
    assert not is_word_instance(token, WORD)


def test_find_word_instances_finds_the_instances_of_every_variant(
    chapter: Chapter,
) -> None:
    found = [
        instance
        for line in chapter.lines
        for instance in find_word_instances(line, WORD)
    ]

    assert find_identities(found) == find_identities(find_instance_tokens(chapter))
    assert [
        index
        for index, line in enumerate(chapter.lines)
        if not find_word_instances(line, WORD)
    ] == list(NO_INSTANCE_INDICES)


@pytest.mark.parametrize("case", COUNT_CASES, ids=lambda case: case[0])
def test_counting_the_instances_of_a_word(chapter: Chapter, case: CountCase) -> None:
    word, words, lemmatized, lines = case

    assert WordInstances.of_lines(chapter.lines, word, REVISION) == WordInstances(
        word, words, lemmatized, lines, REVISION
    )


def test_counting_in_a_chapter_without_lines() -> None:
    assert WordInstances.of_lines((), WORD, REVISION) == WordInstances(
        WORD, 0, 0, (), REVISION
    )


def test_count_of_the_word_lists_the_lines_with_an_instance(chapter: Chapter) -> None:
    instances = WordInstances.of_lines(chapter.lines, WORD, REVISION)

    assert instances.lines == INSTANCE_LINES
    assert len(chapter.lines) == INSTANCES_LINE_COUNT
    assert sorted({*instances.lines, *NO_INSTANCE_INDICES}) == list(
        range(INSTANCES_LINE_COUNT)
    )


def test_word_lemma_holds_the_lemma_as_a_tuple() -> None:
    word_lemma = WordLemma(WORD, list(NEW_LEMMA))

    assert word_lemma == WordLemma(WORD, NEW_LEMMA)
    assert word_lemma.unique_lemma == NEW_LEMMA


@pytest.mark.parametrize(
    "lemma,expected",
    [
        (NEW_LEMMA, True),
        (list(NEW_LEMMA), True),
        (tuple(reversed(NEW_LEMMA)), False),
        (NEW_LEMMA[:1], False),
        ((), False),
    ],
)
def test_word_lemma_is_the_lemma_of_a_word_with_exactly_that_lemma(
    lemma: Lemma, expected: bool
) -> None:
    word = Word.of([], unique_lemma=lemma)

    assert WordLemma(WORD, NEW_LEMMA).is_lemma_of(word) is expected
