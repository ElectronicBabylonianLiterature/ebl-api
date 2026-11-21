from typing import Callable, List, Tuple, cast

import dictdiffer

from ebl.corpus.application.schemas import ChapterSchema, LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_move import LineMove

ChapterDiff = List[Tuple[str, object, object]]
ChapterDiffer = Callable[[Chapter, Chapter], ChapterDiff]


def dump_chapter_document(chapter: Chapter) -> dict:
    return {**cast(dict, ChapterSchema().dump(chapter)), "_id": chapter.id_.to_tuple()}


def create_chapter_diff(old: Chapter, new: Chapter) -> ChapterDiff:
    return list(dictdiffer.diff(dump_chapter_document(old), dump_chapter_document(new)))


def create_line_move_diff(move: LineMove, old: Chapter, new: Chapter) -> ChapterDiff:
    line = LineSchema().dump(old.lines[move.source])
    return [
        (dictdiffer.REMOVE, "lines", [(move.source, line)]),
        (dictdiffer.ADD, "lines", [(move.target, line)]),
        *dictdiffer.diff(_dump_signs(old), _dump_signs(new)),
    ]


def _dump_signs(chapter: Chapter) -> dict:
    return cast(dict, ChapterSchema(only=("signs",)).dump(chapter))
