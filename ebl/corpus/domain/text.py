from typing import Sequence, Union

import attr

from ebl.corpus.domain.chapter import Chapter, Line, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript


TextItem = Union["Text", Chapter, Manuscript, Line, ManuscriptLine]


class TextVisitor:
    def visit(self, item: TextItem) -> None:
        pass


@attr.s(auto_attribs=True, frozen=True)
class TextId:
    category: int
    index: int


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
