from typing import Tuple

import attr

from ebl.corpus.chapter_updater import ChapterUpdater
from ebl.corpus.text import Chapter, Line


class LinesUpdater(ChapterUpdater):

    def __init__(self, chapter_index: int,
                 lines: Tuple[Line, ...]):
        super().__init__(chapter_index)
        self._lines = lines

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return attr.evolve(chapter, lines=self._lines)
