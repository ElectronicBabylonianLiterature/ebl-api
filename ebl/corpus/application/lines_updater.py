from typing import Tuple

import attr

from ebl.atf.domain.atf import ATF_PARSER_VERSION
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.text import Chapter, Line


class LinesUpdater(ChapterUpdater):

    def __init__(self, chapter_index: int,
                 lines: Tuple[Line, ...]):
        super().__init__(chapter_index)
        self._lines = lines

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return chapter.merge(attr.evolve(chapter,
                                         lines=self._lines,
                                         parser_version=ATF_PARSER_VERSION))
