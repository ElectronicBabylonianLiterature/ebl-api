from typing import List, Optional

import attr

from ebl.corpus.text import TextVisitor, Chapter, Text
from ebl.errors import Defect


class ChapterUpdater(TextVisitor):
    def __init__(self, chapter_index: int):
        super().__init__(TextVisitor.Order.POST)
        self._chapters: List[Chapter] = []
        self._text: Optional[Text] = None
        self._chapter_index_to_align = chapter_index

    def get_text(self) -> Text:
        if self._text:
            return self._text
        else:
            raise Defect('get_text called before accepting the visitor.')

    def visit_text(self, text: Text) -> None:
        self._text = attr.evolve(text, chapters=tuple(self._chapters))
        self._chapters = []

    def visit_chapter(self, chapter: Chapter) -> None:
        updated_chapter = (
            self._update_chapter(chapter)
            if self._current_chapter_index == self._chapter_index_to_align
            else chapter
        )

        self._chapters.append(updated_chapter)
        self._after_chapter_update()

    def _after_chapter_update(self) -> None:
        pass

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return chapter

    @property
    def _current_chapter_index(self):
        return len(self._chapters)
