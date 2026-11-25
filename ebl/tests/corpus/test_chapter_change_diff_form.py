from typing import List, cast

import dictdiffer
import pytest

from ebl.corpus.application.chapter_changelog import (
    create_change_diff,
    create_line_diff,
    dump_chapter_document,
)
from ebl.corpus.application.chapter_changes import change_lines
from ebl.corpus.application.schemas import ChapterSchema, LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_change_cases import (
    delete_line,
    MANUSCRIPTS_CASE,
)
from ebl.tests.corpus.chapter_change_support import (
    EDITED,
    FIRST_EDITED_NUMBER,
    FIRST_NEW_NUMBER,
    KEPT,
    create_layout_change,
    create_lines_update,
    create_new_line,
    edit_line,
    insert_line,
    replay,
)
from ebl.tests.corpus.line_move_support import (
    LINE_COUNT,
    create_move_chapter,
)
from ebl.tests.corpus.outline_support import dump_to_dict
from ebl.transliteration.application.sign_repository import SignRepository


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


@pytest.fixture
def dumped_lines(monkeypatch: pytest.MonkeyPatch) -> List[object]:
    dumped: List[object] = []
    dump = LineSchema.dump

    def record_dump(schema: LineSchema, value: object, **kwargs: bool) -> object:
        dumped.append(value)
        return dump(schema, value, **kwargs)

    monkeypatch.setattr(LineSchema, "dump", record_dump)
    return dumped


def dump_line(chapter: Chapter, index: int) -> dict:
    return dump_to_dict(LineSchema(), chapter.lines[index])


def test_line_diff_is_the_diff_of_the_two_dumped_lines(chapter: Chapter) -> None:
    old_line = chapter.lines[1]
    new_line = edit_line(old_line, FIRST_EDITED_NUMBER)

    diff = create_line_diff(3, old_line, new_line)

    assert diff == list(
        dictdiffer.diff(
            dump_to_dict(LineSchema(), old_line),
            dump_to_dict(LineSchema(), new_line),
            node=["lines", 3],
        )
    )
    assert [cast(List[object], path)[:2] for _, path, _ in diff] == [
        ["lines", 3]
    ] * len(diff)
    assert len(diff) > 1


def test_change_diff_orders_edits_removes_adds_and_fields(chapter: Chapter) -> None:
    new_line = create_new_line(FIRST_NEW_NUMBER)
    edited_line = edit_line(chapter.lines[2], FIRST_EDITED_NUMBER)
    change = create_layout_change(
        chapter,
        [new_line, edited_line, chapter.lines[0], chapter.lines[3]],
        [(1, 2), (2, 0), (3, 3)],
        [2],
    )

    diff = create_change_diff(change)

    assert diff == [
        *create_line_diff(2, chapter.lines[2], edited_line),
        ("remove", "lines", [(1, dump_line(chapter, 1)), (0, dump_line(chapter, 0))]),
        (
            "add",
            "lines",
            [(0, dump_to_dict(LineSchema(), new_line)), (2, dump_line(chapter, 0))],
        ),
        *(
            ("change", ["signs", index], (signs, change.new.signs[index]))
            for index, signs in enumerate(chapter.signs)
        ),
        (
            "change",
            "parserVersion",
            (chapter.parser_version, change.new.parser_version),
        ),
    ]
    assert replay(change) == dump_chapter_document(change.new)


def test_change_diff_of_a_manuscripts_update_dumps_the_changed_fields_only(
    registered_sign_repository: SignRepository,
    chapter: Chapter,
    dumped_lines: List[object],
) -> None:
    change = MANUSCRIPTS_CASE.create(chapter, registered_sign_repository)

    assert create_change_diff(change) == [
        entry
        for field in ("manuscripts", "uncertain_fragments")
        for entry in dictdiffer.diff(
            dump_to_dict(ChapterSchema(only=(field,)), chapter),
            dump_to_dict(ChapterSchema(only=(field,)), change.new),
        )
    ]
    assert change.changed_fields == ["manuscripts", "uncertain_fragments"]
    assert dumped_lines == []


@pytest.mark.parametrize("index", range(LINE_COUNT))
def test_change_diff_dumps_only_the_two_forms_of_an_edited_line(
    registered_sign_repository: SignRepository,
    chapter: Chapter,
    dumped_lines: List[object],
    index: int,
) -> None:
    kinds = [EDITED if index == position else KEPT for position in range(LINE_COUNT)]
    change = change_lines(
        create_lines_update(chapter, kinds, 0), registered_sign_repository, chapter
    )

    create_change_diff(change)

    assert dumped_lines == [chapter.lines[index], change.new.lines[index]]


@pytest.mark.parametrize("index", range(LINE_COUNT))
def test_change_diff_dumps_only_the_removed_line(
    registered_sign_repository: SignRepository,
    chapter: Chapter,
    dumped_lines: List[object],
    index: int,
) -> None:
    create_change_diff(delete_line(chapter, index, registered_sign_repository))

    assert dumped_lines == [chapter.lines[index]]


@pytest.mark.parametrize("position", range(LINE_COUNT + 1))
def test_change_diff_dumps_only_the_new_line(
    chapter: Chapter, dumped_lines: List[object], position: int
) -> None:
    change = insert_line(chapter, position)

    create_change_diff(change)

    assert dumped_lines == [change.new.lines[position]]


def test_change_diff_dumps_a_moved_line_that_changed_in_both_forms(
    chapter: Chapter, dumped_lines: List[object]
) -> None:
    moved_line = edit_line(chapter.lines[0], FIRST_EDITED_NUMBER)
    change = create_layout_change(
        chapter, [*chapter.lines[1:], moved_line], tuple(enumerate((1, 2, 3, 0))), [3]
    )

    diff = create_change_diff(change)

    assert dumped_lines == [chapter.lines[0], moved_line]
    assert diff[:2] == [
        ("remove", "lines", [(0, dump_line(chapter, 0))]),
        ("add", "lines", [(3, dump_to_dict(LineSchema(), moved_line))]),
    ]
    assert replay(change) == dump_chapter_document(change.new)
