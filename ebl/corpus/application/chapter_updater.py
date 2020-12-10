from typing import cast, List, Optional

import attr

from ebl.corpus.domain.text import Chapter, Text
from ebl.corpus.domain.text_visitor import TextVisitor
from ebl.errors import DataError, Defect, NotFoundError


class ChapterUpdater(TextVisitor):
    def __init__(self, chapter_index: int):
        super().__init__(TextVisitor.Order.POST)
        self._chapters: List[Chapter] = []
        self._text: Optional[Text] = None
        self._chapter_index_to_align = chapter_index

    def update(self, text: Text) -> Text:
        text.accept(self)
        if self._text is not None:
            return cast(Text, self._text)
        else:
            raise Defect("Result text was not set.")

    def visit_text(self, text: Text) -> None:
        if self._chapter_index_to_align >= len(text.chapters):
            raise NotFoundError(f"Chapter {self._chapter_index_to_align} not found.")

        self._text = attr.evolve(text, chapters=tuple(self._chapters))
        self._chapters = []

    def visit_chapter(self, chapter: Chapter) -> None:
        try:
            updated_chapter = (
                self._update_chapter(chapter)
                if self._current_chapter_index == self._chapter_index_to_align
                else chapter
            )
        except ValueError as error:
            raise DataError(error)

        self._chapters.append(updated_chapter)
        self._after_chapter_update()

    def _after_chapter_update(self) -> None:
        pass

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return chapter

    @property
    def _current_chapter_index(self):
        return len(self._chapters)
