from typing import Sequence

import attr
import pytest

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import (
    CHAPTER_FIELDS,
    KEEP_NOTHING,
    LINES_FIELD,
    ChapterChange,
    KeptContent,
    LineEdit,
    LineRun,
)
from ebl.corpus.domain.line_layout import LineLayout
from ebl.corpus.domain.line_move import LineMove
from ebl.tests.corpus.chapter_change_support import (
    FIRST_EDITED_NUMBER,
    FIRST_NEW_NUMBER,
    OTHER_PARSER_VERSION,
    create_layout_change,
    create_new_line,
    edit_line,
    insert_line,
)
from ebl.tests.corpus.line_annotation_support import replace_item
from ebl.tests.corpus.line_move_support import (
    LINE_COUNT,
    MOVES,
    create_move_chapter,
    move_chapter_line,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

ALL_FIELDS = frozenset({LINES_FIELD, *CHAPTER_FIELDS})


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


def test_chapter_fields() -> None:
    assert CHAPTER_FIELDS == (
        "signs",
        "parser_version",
        "manuscripts",
        "uncertain_fragments",
    )
    assert LINES_FIELD == "lines"
    assert KEEP_NOTHING == KeptContent((), frozenset())


@pytest.mark.parametrize("values", [(-1, 0, 1), (0, -1, 1), (0, 0, 0), (0, 0, -1)])
def test_invalid_line_run(values: Sequence[int]) -> None:
    with pytest.raises(ValueError, match="Invalid line run"):
        LineRun(*values)


def test_line_run_is_extended_by_the_next_line() -> None:
    run = LineRun(2, 5, 3)

    assert run.is_followed_by((5, 8))
    assert not run.is_followed_by((5, 7))
    assert not run.is_followed_by((6, 8))
    assert run.extend() == LineRun(2, 5, 4)


def test_unchanged_chapter_keeps_everything(chapter: Chapter) -> None:
    change = ChapterChange.in_place(chapter, chapter)

    assert change.layout == LineLayout.in_place(LINE_COUNT)
    assert change.changed_fields == []
    assert change.edited == []
    assert change.removed == []
    assert change.added == []
    assert change.unchanged_runs == [LineRun(0, 0, LINE_COUNT)]
    assert change.kept == KeptContent((LineRun(0, 0, LINE_COUNT),), ALL_FIELDS)


def test_unchanged_chapter_without_lines_keeps_everything(chapter: Chapter) -> None:
    empty_chapter = attr.evolve(chapter, lines=())

    assert ChapterChange.in_place(empty_chapter, empty_chapter).kept == KeptContent(
        (), ALL_FIELDS
    )


def test_equal_lines_are_unchanged(chapter: Chapter) -> None:
    rebuilt = attr.evolve(
        chapter,
        lines=tuple(line.set_variant_alignment_flags() for line in chapter.lines),
    )

    change = ChapterChange.in_place(chapter, rebuilt)

    assert all(
        line is not rebuilt.lines[index] and line == rebuilt.lines[index]
        for index, line in enumerate(chapter.lines)
    )
    assert change.edited == []
    assert change.kept == KeptContent((LineRun(0, 0, LINE_COUNT),), ALL_FIELDS)


@pytest.mark.parametrize("index", range(LINE_COUNT))
def test_line_edited_in_place(chapter: Chapter, index: int) -> None:
    edited_line = edit_line(chapter.lines[index], FIRST_EDITED_NUMBER)
    lines = replace_item(chapter.lines, index, edited_line)
    after = LINE_COUNT - index - 1

    change = ChapterChange.in_place(chapter, attr.evolve(chapter, lines=lines))

    assert change.edited == [LineEdit(index, chapter.lines[index], edited_line)]
    assert change.removed == []
    assert change.added == []
    assert change.unchanged_runs == [
        *([LineRun(0, 0, index)] if index else []),
        *([LineRun(index + 1, index + 1, after)] if after else []),
    ]
    assert change.kept.fields == frozenset(CHAPTER_FIELDS)


@pytest.mark.parametrize("position", range(LINE_COUNT + 1))
def test_inserted_line(chapter: Chapter, position: int) -> None:
    after = LINE_COUNT - position

    change = insert_line(chapter, position)

    assert change.edited == []
    assert change.removed == []
    assert change.added == [(position, change.new.lines[position])]
    assert change.new.lines[position] not in chapter.lines
    assert change.unchanged_runs == [
        *([LineRun(0, 0, position)] if position else []),
        *([LineRun(position + 1, position, after)] if after else []),
    ]
    assert change.changed_fields == ["signs", "parser_version"]
    assert change.kept.fields == {"manuscripts", "uncertain_fragments"}


@pytest.mark.parametrize("position", range(LINE_COUNT))
def test_removed_line(chapter: Chapter, position: int) -> None:
    sources = [index for index in range(LINE_COUNT) if index != position]
    after = LINE_COUNT - position - 1

    change = create_layout_change(
        chapter,
        [chapter.lines[index] for index in sources],
        tuple(enumerate(sources)),
    )

    assert change.removed == [(position, chapter.lines[position])]
    assert change.added == []
    assert change.unchanged_runs == [
        *([LineRun(0, 0, position)] if position else []),
        *([LineRun(position, position + 1, after)] if after else []),
    ]
    assert LINES_FIELD not in change.kept.fields


@pytest.mark.parametrize("move", MOVES)
def test_moved_line_is_a_run_of_its_own(chapter: Chapter, move: LineMove) -> None:
    moved_chapter = move_chapter_line(chapter, move)
    line = chapter.lines[move.source]

    change = ChapterChange(chapter, moved_chapter, move.create_layout(LINE_COUNT))
    runs = change.unchanged_runs

    assert change.edited == []
    assert change.removed == [(move.source, line)]
    assert change.added == [(move.target, line)]
    assert LineRun(move.target, move.source, 1) in runs
    assert sum(run.count for run in runs) == LINE_COUNT
    assert [
        chapter.lines[run.source + offset]
        for run in runs
        for offset in range(run.count)
    ] == list(moved_chapter.lines)
    assert change.kept == KeptContent(
        tuple(runs), frozenset({"parser_version", "manuscripts", "uncertain_fragments"})
    )


def test_mixed_change(chapter: Chapter) -> None:
    new_line = create_new_line(FIRST_NEW_NUMBER)
    edited_line = edit_line(chapter.lines[2], FIRST_EDITED_NUMBER)
    moved_line = edit_line(chapter.lines[0], FIRST_EDITED_NUMBER + 1)

    change = create_layout_change(
        chapter,
        [new_line, edited_line, moved_line, chapter.lines[3]],
        [(1, 2), (2, 0), (3, 3)],
        [2],
    )

    assert change.edited == [LineEdit(2, chapter.lines[2], edited_line)]
    assert change.removed == [(1, chapter.lines[1]), (0, chapter.lines[0])]
    assert change.added == [(0, new_line), (2, moved_line)]
    assert change.unchanged_runs == [LineRun(3, 3, 1)]


def test_every_changed_field_is_found(chapter: Chapter) -> None:
    changed_chapter = attr.evolve(
        chapter,
        signs=("KU",),
        parser_version=OTHER_PARSER_VERSION,
        manuscripts=tuple(reversed(chapter.manuscripts)),
        uncertain_fragments=(MuseumNumber.of("K.7"),),
    )

    change = ChapterChange.in_place(chapter, changed_chapter)

    assert change.changed_fields == list(CHAPTER_FIELDS)
    assert change.kept == KeptContent((LineRun(0, 0, LINE_COUNT),), {LINES_FIELD})


@pytest.mark.parametrize(
    "layout",
    [
        LineLayout.in_place(3),
        LineLayout.of_sources(range(LINE_COUNT), 1),
        LineLayout.of_sources((0, 1, 2, LINE_COUNT)),
    ],
)
def test_layout_that_does_not_fit_the_chapters(
    chapter: Chapter, layout: LineLayout
) -> None:
    with pytest.raises(ValueError, match="does not fit a change from 4 to 4 lines"):
        ChapterChange(chapter, chapter, layout)
