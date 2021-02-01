from typing import Sequence, Union

import attr
import roman  # pyre-ignore[21]

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

    def __str__(self) -> str:
        return (
            f"{self.category}.{self.index}"
            if self.category < 1
            else f"{roman.toRoman(self.category)}.{self.index}"
        )


@attr.s(auto_attribs=True, frozen=True)
class ChapterId:
    text_id: TextId
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
