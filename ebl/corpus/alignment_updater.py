from typing import List, Optional

import attr

from ebl.corpus.alignment import Alignment
from ebl.corpus.text import TextVisitor, Text, Chapter, Line, ManuscriptLine
from ebl.errors import Defect


class AlignmentUpdater(TextVisitor):

    def __init__(self, chapter_index: int, alignment: Alignment):
        super().__init__(TextVisitor.Order.POST)
        self._alignment = alignment
        self._chapter_index_to_align = chapter_index
        self._text: Optional[Text] = None
        self._chapters: List[Chapter] = []
        self._lines: List[Line] = []
        self._manuscript_lines: List[ManuscriptLine] = []

    @property
    def chapter_index(self):
        return len(self._chapters)

    @property
    def line_index(self):
        return len(self._lines)

    @property
    def manuscript_line_index(self):
        return len(self._manuscript_lines)

    @property
    def current_alignment(self):
        return self._alignment.get_manuscript_line(self.line_index,
                                                   self.manuscript_line_index)

    def get_text(self) -> Text:
        if self._text:
            return self._text
        else:
            raise Defect('get_text called before accepting the visitor.')

    def visit_text(self, text: Text) -> None:
        self._text = attr.evolve(text, chapters=tuple(self._chapters))
        self._chapters = []

    def visit_chapter(self, chapter: Chapter) -> None:
        self._chapters.append(
            attr.evolve(chapter, lines=tuple(self._lines))
            if self.chapter_index == self._chapter_index_to_align
            else chapter
        )
        self._lines = []

    def visit_line(self, line: Line) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            self._lines.append(
                attr.evolve(line, manuscripts=tuple(self._manuscript_lines))
            )
            self._manuscript_lines = []

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            updated_line = manuscript_line.line.update_alignment(
                self.current_alignment
            )
            self._manuscript_lines.append(
                attr.evolve(
                    manuscript_line,
                    line=updated_line
                )
            )
