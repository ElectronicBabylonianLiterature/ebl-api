from typing import Sequence

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter, Line
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION


class LinesUpdater(ChapterUpdater):
    def __init__(self, chapter_index: int, lines: Sequence[Line]):
        super().__init__(chapter_index)
        self._lines = lines

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return chapter.merge(
            attr.evolve(chapter, lines=self._lines, parser_version=ATF_PARSER_VERSION)
        )
