from abc import abstractmethod
from typing import Sequence

import attr

from ebl.corpus.domain.chapter import Chapter, VisitChapter


@attr.s(auto_attribs=True, frozen=True)
class TextId:
    category: int
    index: int


class VisitText(VisitChapter):
    @abstractmethod
    def visit_text(self, text: "Text") -> None:
        ...


@attr.s(auto_attribs=True, frozen=True)
class Text:
    category: int
    index: int
    name: str
    number_of_verses: int
    approximate_verses: bool
    chapters: Sequence[Chapter] = tuple()

    @property
    def id(self) -> TextId:
        return TextId(self.category, self.index)

    def accept(self, visitor: VisitText) -> None:
        if visitor.is_pre_order:
            visitor.visit_text(self)

        for chapter in self.chapters:
            chapter.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_text(self)
