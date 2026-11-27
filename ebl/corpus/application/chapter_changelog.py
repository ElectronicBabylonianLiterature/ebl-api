from typing import Dict, List, Sequence, Tuple, cast

import dictdiffer

from ebl.corpus.application.schemas import ChapterSchema, LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import LINES_FIELD, ChapterChange, PositionedLine
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_move import LineMove

ChapterDiff = List[Tuple[str, object, object]]
PositionedDump = Tuple[int, dict]


def dump_chapter_document(chapter: Chapter) -> dict:
    return {**cast(dict, ChapterSchema().dump(chapter)), "_id": chapter.id_.to_tuple()}


def create_chapter_diff(old: Chapter, new: Chapter) -> ChapterDiff:
    return list(dictdiffer.diff(dump_chapter_document(old), dump_chapter_document(new)))


def _dump_line(line: Line) -> dict:
    return cast(dict, LineSchema().dump(line))


def _dump_field(chapter: Chapter, field: str) -> dict:
    return cast(dict, ChapterSchema(only=(field,)).dump(chapter))


class _LineDumps:
    def __init__(self) -> None:
        self._dumps: Dict[int, dict] = {}

    def dump(self, lines: Sequence[PositionedLine]) -> List[PositionedDump]:
        return [(position, self._dump_once(line)) for position, line in lines]

    def _dump_once(self, line: Line) -> dict:
        if id(line) not in self._dumps:
            self._dumps[id(line)] = _dump_line(line)
        return self._dumps[id(line)]


def create_line_diff(position: int, old: Line, new: Line) -> ChapterDiff:
    return list(
        dictdiffer.diff(_dump_line(old), _dump_line(new), node=[LINES_FIELD, position])
    )


def _create_layout_diff(change: ChapterChange) -> ChapterDiff:
    dumps = _LineDumps()
    return [
        (action, LINES_FIELD, lines)
        for action, lines in (
            (dictdiffer.REMOVE, dumps.dump(change.removed)),
            (dictdiffer.ADD, dumps.dump(change.added)),
        )
        if lines
    ]


def _create_field_diff(change: ChapterChange, field: str) -> ChapterDiff:
    return list(
        dictdiffer.diff(_dump_field(change.old, field), _dump_field(change.new, field))
    )


def create_change_diff(change: ChapterChange) -> ChapterDiff:
    return [
        *(
            entry
            for edit in change.edited
            for entry in create_line_diff(edit.position, edit.old, edit.new)
        ),
        *_create_layout_diff(change),
        *(
            entry
            for field in change.changed_fields
            for entry in _create_field_diff(change, field)
        ),
    ]


def create_line_move_diff(move: LineMove, old: Chapter, new: Chapter) -> ChapterDiff:
    return create_change_diff(
        ChapterChange(old, new, move.create_layout(len(old.lines)))
    )
