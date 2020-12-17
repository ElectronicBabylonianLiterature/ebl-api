from typing import cast, List, Optional

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.text import Text, TextItem, TextVisitor
from ebl.errors import DataError, Defect, NotFoundError


class ChapterUpdater(TextVisitor):
    def __init__(self, chapter_index: int):
        self._chapters: List[Chapter] = []
        self._text: Optional[Text] = None
        self._chapter_index_to_align = chapter_index

    def update(self, text: Text) -> Text:
        self.visit(text)
        if self._text is not None:
            return cast(Text, self._text)
        else:
            raise Defect("Result text was not set.")

    @singledispatchmethod  # pyre-ignore[56]
    def visit(self, item: TextItem) -> None:
        pass

    @visit.register(Text)  # pyre-ignore[56]
    def _visit_text(self, text: Text) -> None:
        for chapter in text.chapters:
            self.visit(chapter)

        if self._chapter_index_to_align >= len(text.chapters):
            raise NotFoundError(f"Chapter {self._chapter_index_to_align} not found.")

        self._text = attr.evolve(text, chapters=tuple(self._chapters))
        self._chapters = []

    @visit.register(Chapter)  # pyre-ignore[56]
    def _visit_chapter(self, chapter: Chapter) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            for manuscript in chapter.manuscripts:
                self.visit(manuscript)

            for line in chapter.lines:
                self.visit(line)

            try:
                updated_chapter = (
                    self._update_chapter(chapter)
                    if self._current_chapter_index == self._chapter_index_to_align
                    else chapter
                )
            except ValueError as error:
                raise DataError(error)

            self._chapters.append(updated_chapter)
        else:
            self._chapters.append(chapter)

        self._after_chapter_update()

    def _after_chapter_update(self) -> None:
        pass

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return chapter

    @property
    def _current_chapter_index(self):
        return len(self._chapters)
