from typing import Callable, Optional

import pytest

from ebl.corpus.application.alignment_updater import LineAlignmentUpdater
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.application.lemmatization_updater import LineLemmatizationUpdater
from ebl.corpus.domain.alignment import LineAlignment
from ebl.corpus.domain.chapter import Chapter
from ebl.errors import DataError
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.tests.corpus.line_annotation_kind import (
    AnnotationKind,
    ChapterUpdate,
    InvalidAnnotation,
    matches,
)
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, LEMMATIZATION
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    create_annotation_chapter,
)
from ebl.tests.corpus.line_move_support import LINE_COUNT
from ebl.transliteration.domain.alignment import AlignmentError

INVALID_POSITION = "Invalid line: {} is not a line position (number of lines: 5)."
LINE_UPDATERS = (
    lambda index: LineAlignmentUpdater(LineAlignment(index, ())),
    lambda index: LineLemmatizationUpdater(LineLemmatization(index, ())),
)


@pytest.fixture
def chapter() -> Chapter:
    return create_annotation_chapter()


def find_error(update: ChapterUpdate, chapter: Chapter) -> Optional[str]:
    try:
        update(chapter)
    except (AlignmentError, LemmatizationError) as error:
        return str(error)
    return None


def test_invalid_annotation_of_a_line_is_refused_with_a_message(
    chapter: Chapter, invalid_annotation: InvalidAnnotation
) -> None:
    message = find_error(invalid_annotation.update_line, chapter)

    assert message is not None
    assert matches(invalid_annotation.line_error, message)


def test_chapter_updater_keeps_its_errors(
    chapter: Chapter, invalid_annotation: InvalidAnnotation
) -> None:
    message = find_error(invalid_annotation.update_chapter, chapter)

    assert matches(invalid_annotation.chapter_error, message)


@pytest.mark.parametrize("create_updater", LINE_UPDATERS)
@pytest.mark.parametrize("index", [ANNOTATION_LINE_COUNT, -1, 10**20])
def test_line_position_out_of_range(
    chapter: Chapter, create_updater: Callable[[int], ChapterUpdater], index: int
) -> None:
    with pytest.raises(DataError) as error:
        create_updater(index).update(chapter)

    assert str(error.value) == INVALID_POSITION.format(index)


@pytest.mark.parametrize(
    "kind,message",
    [
        (ALIGNMENT, "Invalid number of lines. Got 4, expected 5."),
        (LEMMATIZATION, "Invalid lemmatization"),
    ],
    ids=lambda value: getattr(value, "name", ""),
)
def test_chapter_updater_requires_every_line(
    chapter: Chapter, kind: AnnotationKind, message: str
) -> None:
    updater = kind.create_chapter_updater(
        [kind.find(line) for line in chapter.lines[:LINE_COUNT]]
    )

    with pytest.raises((AlignmentError, LemmatizationError)) as error:
        updater.update(chapter)

    assert str(error.value) == message
