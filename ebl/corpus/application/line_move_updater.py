import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_move import LineMove
from ebl.transliteration.application.sign_repository import SignRepository


class LineMoveUpdater(ChapterUpdater):
    def __init__(self, move: LineMove, sign_repository: SignRepository) -> None:
        super().__init__()
        self._move = move
        self._sign_updater = SignsUpdater(sign_repository)

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return self._sign_updater.update(
            attr.evolve(chapter, lines=self._move.apply(chapter.lines))
        )
