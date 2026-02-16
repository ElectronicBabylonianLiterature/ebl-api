from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import Optional

from ebl.corpus.domain.chapter import Chapter, ChapterItem, ChapterVisitor
from ebl.errors import DataError, Defect


class ChapterUpdater(ABC, ChapterVisitor):
    def __init__(self):
        self._chapter: Optional[Chapter] = None

    def update(self, chapter: Chapter) -> Chapter:
        self.visit(chapter)
        if self._chapter is not None:
            return self._chapter
        else:
            raise Defect("Result chapter was not set.")

    @abstractmethod
    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return chapter

    @singledispatchmethod
    def visit(self, item: ChapterItem) -> None:
        pass

    @visit.register(Chapter)
    def _visit_chapter(self, chapter: Chapter) -> None:
        self._validate_chapter(chapter)
        self._visit_manuscripts(chapter)
        self._visit_lines(chapter)
        self._chapter = self._try_update_chapter(chapter)

        self._after_chapter_update()

    def _visit_manuscripts(self, chapter: Chapter) -> None:
        for manuscript in chapter.manuscripts:
            self.visit(manuscript)

    def _visit_lines(self, chapter: Chapter) -> None:
        for line in chapter.lines:
            self.visit(line)

    def _after_chapter_update(self) -> None:
        pass

    def _try_update_chapter(self, chapter: Chapter) -> Chapter:
        try:
            return self._update_chapter(chapter)
        except ValueError as error:
            raise DataError(error)

    def _validate_chapter(self, chapter: Chapter) -> None:
        pass
