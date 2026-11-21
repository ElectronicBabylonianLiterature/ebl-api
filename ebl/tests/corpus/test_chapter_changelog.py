from typing import List, Sequence

import attr
import dictdiffer
import pytest

from ebl.corpus.application.chapter_changelog import (
    create_chapter_diff,
    create_line_move_diff,
    dump_chapter_document,
)
from ebl.corpus.application.schemas import ChapterSchema, LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_move import LineMove
from ebl.tests.corpus.line_move_support import (
    LONG_LINE_COUNT,
    LONG_MOVE,
    MOVE,
    MOVES,
    SHORT_MOVE,
    create_move_chapter,
    find_diff_size,
    move_chapter_line,
)
from ebl.tests.corpus.lines_edit_support import EDITED_INDEX, update_chapter
from ebl.tests.corpus.outline_support import dump_to_dict

OTHER_SIGNS = "TA MI\nKU"


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


def test_chapter_document_is_the_dumped_chapter_with_its_id(chapter: Chapter) -> None:
    assert dump_chapter_document(chapter) == {
        **dump_to_dict(ChapterSchema(), chapter),
        "_id": chapter.id_.to_tuple(),
    }


def test_chapter_diff_replays_the_change(chapter: Chapter) -> None:
    updated_chapter = update_chapter(chapter, EDITED_INDEX)
    old_document = dump_chapter_document(chapter)
    new_document = dump_chapter_document(updated_chapter)

    diff = create_chapter_diff(chapter, updated_chapter)

    assert dictdiffer.patch(diff, old_document) == new_document
    assert new_document != old_document


def test_chapter_diff_of_an_unchanged_chapter_is_empty(chapter: Chapter) -> None:
    assert create_chapter_diff(chapter, chapter) == []


@pytest.mark.parametrize("move", MOVES)
def test_line_move_diff_replays_the_move(chapter: Chapter, move: LineMove) -> None:
    moved_chapter = move_chapter_line(chapter, move)
    old_document = dump_chapter_document(chapter)
    new_document = dump_chapter_document(moved_chapter)

    diff = create_line_move_diff(move, chapter, moved_chapter)

    assert dictdiffer.patch(diff, old_document) == new_document
    assert new_document["lines"] != old_document["lines"]
    assert set(new_document["signs"]).isdisjoint(old_document["signs"])


@pytest.mark.parametrize("move", MOVES)
def test_line_move_diff_equals_the_chapter_diff_when_replayed(
    chapter: Chapter, move: LineMove
) -> None:
    moved_chapter = move_chapter_line(chapter, move)
    old_document = dump_chapter_document(chapter)

    assert dictdiffer.patch(
        create_line_move_diff(move, chapter, moved_chapter), old_document
    ) == dictdiffer.patch(create_chapter_diff(chapter, moved_chapter), old_document)


@pytest.mark.parametrize("move", MOVES)
def test_line_move_diff_is_undone_in_reverse_order(
    chapter: Chapter, move: LineMove
) -> None:
    moved_chapter = move_chapter_line(chapter, move)
    diff = create_line_move_diff(move, chapter, moved_chapter)

    assert dictdiffer.patch(
        reversed(list(dictdiffer.swap(diff))), dump_chapter_document(moved_chapter)
    ) == dump_chapter_document(chapter)


def test_line_move_diff_moves_the_line_and_changes_the_signs(chapter: Chapter) -> None:
    moved_chapter = move_chapter_line(chapter, MOVE)
    line = dump_chapter_document(chapter)["lines"][MOVE.source]

    assert create_line_move_diff(MOVE, chapter, moved_chapter) == [
        ("remove", "lines", [(MOVE.source, line)]),
        ("add", "lines", [(MOVE.target, line)]),
        ("change", ["signs", 0], (chapter.signs[0], moved_chapter.signs[0])),
        ("change", ["signs", 1], (chapter.signs[1], moved_chapter.signs[1])),
    ]


@pytest.mark.parametrize("changed_indexes", [(), (0,), (1,), (0, 1)])
def test_line_move_diff_changes_only_the_signs_that_differ(
    chapter: Chapter, changed_indexes: Sequence[int]
) -> None:
    signs = tuple(
        OTHER_SIGNS if index in changed_indexes else manuscript_signs
        for index, manuscript_signs in enumerate(chapter.signs)
    )
    moved_chapter = attr.evolve(move_chapter_line(chapter, MOVE), signs=signs)

    diff = create_line_move_diff(MOVE, chapter, moved_chapter)

    assert diff[2:] == [
        ("change", ["signs", index], (chapter.signs[index], OTHER_SIGNS))
        for index in changed_indexes
    ]
    assert dictdiffer.patch(
        diff, dump_chapter_document(chapter)
    ) == dump_chapter_document(moved_chapter)


def test_line_move_diff_dumps_only_the_moved_line(
    chapter: Chapter, monkeypatch: pytest.MonkeyPatch
) -> None:
    dumped: List[object] = []
    dump = LineSchema.dump

    def record_dump(schema: LineSchema, value: object, **kwargs: bool) -> object:
        dumped.append(value)
        return dump(schema, value, **kwargs)

    monkeypatch.setattr(LineSchema, "dump", record_dump)

    create_line_move_diff(MOVE, chapter, move_chapter_line(chapter, MOVE))

    assert dumped == [chapter.lines[MOVE.source]]


def test_line_move_diff_does_not_grow_with_the_distance() -> None:
    chapter = create_move_chapter(LONG_LINE_COUNT)
    short_diff, long_diff = (
        create_line_move_diff(move, chapter, move_chapter_line(chapter, move))
        for move in (SHORT_MOVE, LONG_MOVE)
    )

    assert find_diff_size(long_diff) == find_diff_size(short_diff)


def test_chapter_diff_grows_with_the_distance() -> None:
    chapter = create_move_chapter(LONG_LINE_COUNT)
    short_size, long_size = (
        find_diff_size(create_chapter_diff(chapter, move_chapter_line(chapter, move)))
        for move in (SHORT_MOVE, LONG_MOVE)
    )

    assert long_size > 10 * short_size
