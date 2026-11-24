from typing import Callable

import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_outline import ChapterOutline


@attr.s(frozen=True, auto_attribs=True)
class SavedChapter:
    revision: str
    _find_chapter: Callable[[], Chapter]
    _find_outline: Callable[[], ChapterOutline]

    @staticmethod
    def of_chapter(chapter: Chapter, revision: str) -> "SavedChapter":
        return SavedChapter(
            revision,
            lambda: chapter,
            lambda: ChapterOutline.of_chapter(chapter, revision),
        )

    @property
    def chapter(self) -> Chapter:
        return self._find_chapter()

    @property
    def outline(self) -> ChapterOutline:
        return self._find_outline()
