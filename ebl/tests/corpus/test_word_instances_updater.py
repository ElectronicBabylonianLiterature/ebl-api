import re
from typing import List, Tuple

import pytest

from ebl.corpus.application.lemmatization_updater import LemmatizationUpdater
from ebl.corpus.application.word_instances_updater import (
    NO_LEMMA_CHANGE,
    NO_WORD_INSTANCE,
    WordInstancesLemmatizer,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.word_instances import WordLemma
from ebl.errors import DataError
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.line_annotation_support import (
    create_annotation_chapter,
    find_line_alignment,
)
from ebl.tests.corpus.line_move_support import LEMMA, find_words
from ebl.tests.corpus.word_instances_reference import (
    create_chapter_lemmatization,
    lemmatize_instances,
)
from ebl.tests.corpus.word_instances_support import (
    INSTANCES_LINE_COUNT,
    NEW_LEMMA,
    NO_INSTANCE_INDICES,
    WORD,
    WORDS_WITHOUT_INSTANCE,
    create_instances_chapter,
)

Flags = Tuple[bool, bool]


@pytest.fixture
def chapter() -> Chapter:
    return create_instances_chapter()


def lemmatize(chapter: Chapter, word: str = WORD, lemma: Lemma = NEW_LEMMA) -> Chapter:
    return WordInstancesLemmatizer(WordLemma(word, lemma)).update(chapter)


def find_flags(line: Line) -> List[List[Flags]]:
    return [
        [
            (word.has_variant_alignment, word.has_omitted_alignment)
            for word in find_words(variant.reconstruction)
        ]
        for variant in line.variants
    ]


def test_every_instance_gets_the_lemma_and_nothing_else_changes(
    chapter: Chapter,
) -> None:
    updated_chapter = lemmatize(chapter)

    assert updated_chapter == lemmatize_instances(chapter)
    assert updated_chapter != chapter


def test_lines_without_an_instance_are_the_same_objects(chapter: Chapter) -> None:
    updated_chapter = lemmatize(chapter)

    assert [
        updated_line is chapter.lines[index]
        for index, updated_line in enumerate(updated_chapter.lines)
    ] == [index in NO_INSTANCE_INDICES for index in range(INSTANCES_LINE_COUNT)]


def test_alignment_flags_and_the_rest_of_the_chapter_are_kept(chapter: Chapter) -> None:
    updated_chapter = lemmatize(chapter)

    assert list(map(find_line_alignment, updated_chapter.lines)) == list(
        map(find_line_alignment, chapter.lines)
    )
    assert list(map(find_flags, updated_chapter.lines)) == list(
        map(find_flags, chapter.lines)
    )
    assert any(
        any(flags) for line in chapter.lines for flags in sum(find_flags(line), [])
    )
    assert updated_chapter.signs == chapter.signs
    assert updated_chapter.parser_version == chapter.parser_version
    assert updated_chapter.manuscripts == chapter.manuscripts


@pytest.mark.parametrize("word", [*WORDS_WITHOUT_INSTANCE, ""])
def test_word_without_an_instance_is_refused(chapter: Chapter, word: str) -> None:
    with pytest.raises(DataError, match=re.escape(NO_WORD_INSTANCE.format(word))):
        lemmatize(chapter, word)


def test_lemma_that_every_instance_already_has_is_refused(chapter: Chapter) -> None:
    updated_chapter = lemmatize(chapter)
    message = NO_LEMMA_CHANGE.format(WORD, "ana I, ana II")

    with pytest.raises(DataError, match=re.escape(message)):
        lemmatize(updated_chapter)
    with pytest.raises(
        DataError, match=re.escape(NO_LEMMA_CHANGE.format("ku", LEMMA[0]))
    ):
        lemmatize(chapter, "ku", LEMMA)


def test_lemma_in_another_order_replaces_the_lemma(chapter: Chapter) -> None:
    reversed_lemma: Lemma = tuple(reversed(NEW_LEMMA))
    updated_chapter = lemmatize(chapter)

    assert lemmatize(updated_chapter, WORD, reversed_lemma) == lemmatize_instances(
        chapter, reversed_lemma
    )


@pytest.mark.parametrize("word", ["buāru", "eliš", "ku", "nu"])
def test_update_equals_the_lemmatization_updater_with_the_lemma_at_every_instance(
    word: str,
) -> None:
    chapter = create_annotation_chapter()
    lemmatization = create_chapter_lemmatization(chapter, word)

    updated_chapter = lemmatize(chapter, word)

    assert updated_chapter == LemmatizationUpdater(lemmatization).update(chapter)
    assert updated_chapter != chapter
