from typing import Sequence

import attr
import pytest

from ebl.corpus.application.chapter_updater import ChapterUpdater, try_update
from ebl.corpus.application.text_validator import TextValidator, validate_line
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.errors import DataError, Defect
from ebl.tests.corpus.line_annotation_support import replace_item
from ebl.tests.corpus.line_move_support import ALIGNED_INDEX, create_move_chapter
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import Word

INVALID_INDEX = 2
REFUSAL = "refused by the update"
DUPLICATES: Sequence[Sequence[Token]] = (
    tuple(Word.of([Reading.of_name("ku")], alignment=ALIGNED_INDEX) for _ in range(2)),
    tuple(
        GreekWord.of([GreekLetter.of("α")], alignment=ALIGNED_INDEX) for _ in range(2)
    ),
)


class ForgettingUpdater(ChapterUpdater):
    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return super()._update_chapter(chapter)

    def _after_chapter_update(self) -> None:
        self._chapter = None


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


def refuse() -> None:
    raise ValueError(REFUSAL)


def set_content(line: Line, content: Sequence[Token]) -> Line:
    variant = line.variants[0]
    manuscript_line = attr.evolve(
        variant.manuscripts[1],
        line=TextLine.of_iterable(LineNumber(INVALID_INDEX + 1), content),
    )
    return attr.evolve(
        line,
        variants=(
            attr.evolve(variant, manuscripts=(variant.manuscripts[0], manuscript_line)),
        ),
    )


def create_message(chapter: Chapter) -> str:
    number = chapter.lines[INVALID_INDEX].number.atf
    return f"Invalid line {number} {chapter.manuscripts[1].siglum}. [{ALIGNED_INDEX}]"


def test_try_update_returns_the_update() -> None:
    assert try_update(lambda: 3) == 3


def test_try_update_reports_an_invalid_value_as_a_data_error() -> None:
    with pytest.raises(DataError, match=REFUSAL):
        try_update(refuse)


def test_updater_that_sets_no_chapter_is_a_defect(chapter: Chapter) -> None:
    with pytest.raises(Defect, match="Result chapter was not set"):
        ForgettingUpdater().update(chapter)


def test_words_without_alignment_pass(chapter: Chapter) -> None:
    content = (
        GreekWord.of([GreekLetter.of("α")]),
        GreekWord.of([GreekLetter.of("β")], alignment=ALIGNED_INDEX),
        Word.of([Reading.of_name("ku")]),
    )

    validate_line(set_content(chapter.lines[INVALID_INDEX], content), ())


def test_valid_lines_pass(chapter: Chapter) -> None:
    for line in chapter.lines:
        validate_line(line, chapter.manuscripts)
    TextValidator().visit(chapter)


@pytest.mark.parametrize("content", DUPLICATES, ids=["word", "greek word"])
def test_duplicate_alignment_indices_of_a_line_are_refused_with_the_siglum(
    chapter: Chapter, content: Sequence[Token]
) -> None:
    line = set_content(chapter.lines[INVALID_INDEX], content)

    with pytest.raises(DataError) as error:
        validate_line(line, chapter.manuscripts)

    assert str(error.value) == create_message(chapter)


@pytest.mark.parametrize("content", DUPLICATES, ids=["word", "greek word"])
def test_validator_refuses_a_chapter_like_its_line(
    chapter: Chapter, content: Sequence[Token]
) -> None:
    line = set_content(chapter.lines[INVALID_INDEX], content)
    invalid_chapter = attr.evolve(
        chapter, lines=replace_item(chapter.lines, INVALID_INDEX, line)
    )

    with pytest.raises(DataError) as error:
        TextValidator().visit(invalid_chapter)

    assert str(error.value) == create_message(chapter)


def test_validator_needs_a_chapter_for_a_line(chapter: Chapter) -> None:
    with pytest.raises(Defect, match="access chapter before a chapter was visited"):
        TextValidator().visit(chapter.lines[0])


def test_validator_needs_a_line_for_a_manuscript_line(chapter: Chapter) -> None:
    with pytest.raises(Defect, match="access line before a line was visited"):
        TextValidator().visit(chapter.lines[0].variants[0].manuscripts[0])
