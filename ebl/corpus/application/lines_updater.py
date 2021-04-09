from typing import Sequence

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter, Line
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, WORD_SEPARATOR
from ebl.transliteration.domain.text import TextLine
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)


class LinesUpdater(ChapterUpdater):
    def __init__(
        self, chapter_index: int, lines: Sequence[Line], sing_repository: SignRepository
    ):
        super().__init__(chapter_index)
        self._lines = lines
        self._sing_repository = MemoizingSignRepository(sing_repository)

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        merged_chapter = chapter.merge(
            attr.evolve(chapter, lines=self._lines, parser_version=ATF_PARSER_VERSION)
        )
        signs = tuple(
            self._map_lines(merged_chapter.get_manuscript_text_lines(manuscript))
            for manuscript in merged_chapter.manuscripts
        )
        return attr.evolve(merged_chapter, signs=signs)

    def _map_lines(self, lines: Sequence[TextLine]) -> str:
        return "\n".join(self._map_line(line) for line in lines)

    def _map_line(self, line: TextLine) -> str:
        visitor = SignsVisitor(self._sing_repository)
        line.accept(visitor)
        return WORD_SEPARATOR.join(visitor.result)
