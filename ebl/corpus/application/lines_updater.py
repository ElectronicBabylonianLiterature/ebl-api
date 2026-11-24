from typing import List

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION


class LinesUpdater(ChapterUpdater):
    def __init__(self, lines: LinesUpdate, sign_repository: SignRepository):
        super().__init__()
        self._lines_update = lines
        self._sign_updater = SignsUpdater(sign_repository)
        self._lines: List[Line] = []

    def _visit_lines(self, chapter: Chapter) -> None:
        edited = self._lines_update.edited
        self._lines = [
            edited.get(index, chapter.lines[index]).set_variant_alignment_flags()
            for index in self._lines_update.find_kept(len(chapter.lines))
        ]

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return self._sign_updater.update(
            chapter.merge(
                attr.evolve(
                    chapter,
                    lines=(*self._lines, *self._lines_update.new),  # pyre-ignore[60]
                    parser_version=ATF_PARSER_VERSION,
                )
            )
        )
