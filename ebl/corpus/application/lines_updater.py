from typing import Sequence

import attr
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter, Line
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION


class LinesUpdater(ChapterUpdater):
    def __init__(
        self, chapter_index: int, lines: Sequence[Line], sing_repository: SignRepository
    ):
        super().__init__(chapter_index)
        self._lines = lines
        self._sing_updater = SignsUpdater(sing_repository)

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return self._sing_updater.update(
            chapter.merge(
                attr.evolve(
                    chapter, lines=self._lines, parser_version=ATF_PARSER_VERSION
                )
            )
        )
