from typing import List

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.text import Chapter, Line, ManuscriptLine
from ebl.transliteration.domain.alignment import AlignmentError
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment


class AlignmentUpdater(ChapterUpdater):
    def __init__(self, chapter_index: int, alignment: Alignment):
        super().__init__(chapter_index)
        self._alignment = alignment
        self._lines: List[Line] = []
        self._manuscript_lines: List[ManuscriptLine] = []

    @property
    def line_index(self) -> int:
        return len(self._lines)

    @property
    def manuscript_line_index(self) -> int:
        return len(self._manuscript_lines)

    @property
    def current_alignment(self) -> ManuscriptLineAlignment:
        try:
            return self._alignment.get_manuscript_line(
                self.line_index, self.manuscript_line_index
            )
        except IndexError:
            raise AlignmentError()

    def visit_line(self, line: Line) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            if self._alignment.get_number_of_manuscripts(self.line_index) == len(
                line.manuscripts
            ):
                self._lines.append(
                    attr.evolve(line, manuscripts=tuple(self._manuscript_lines))
                )
                self._manuscript_lines = []
            else:
                raise AlignmentError()

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            updated_line = manuscript_line.line.update_alignment(
                self.current_alignment.alignment
            )
            self._manuscript_lines.append(
                attr.evolve(
                    manuscript_line,
                    line=updated_line,
                    omitted_words=self.current_alignment.omitted_words,
                )
            )

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        if self._alignment.get_number_of_lines() == len(chapter.lines):
            return attr.evolve(chapter, lines=tuple(self._lines))
        else:
            raise AlignmentError()

    def _after_chapter_update(self) -> None:
        self._lines = []
