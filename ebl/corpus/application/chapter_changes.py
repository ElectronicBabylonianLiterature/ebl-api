from typing import Callable

from ebl.corpus.application.line_move_updater import LineMoveUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.transliteration.application.sign_repository import SignRepository

ChapterUpdate = Callable[[Chapter], Chapter]
ChapterChanger = Callable[[Chapter], ChapterChange]


def change_in_place(update: ChapterUpdate, chapter: Chapter) -> ChapterChange:
    return ChapterChange.in_place(chapter, update(chapter))


def change_lines(
    lines: LinesUpdate, sign_repository: SignRepository, chapter: Chapter
) -> ChapterChange:
    return ChapterChange(
        chapter,
        LinesUpdater(lines, sign_repository).update(chapter),
        lines.create_layout(len(chapter.lines)),
    )


def move_line(
    move: LineMove, sign_repository: SignRepository, chapter: Chapter
) -> ChapterChange:
    return ChapterChange(
        chapter,
        LineMoveUpdater(move, sign_repository).update(chapter),
        move.create_layout(len(chapter.lines)),
    )
