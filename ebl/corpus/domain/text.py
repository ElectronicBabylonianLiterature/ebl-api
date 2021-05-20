from typing import Sequence

import attr

from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId


@attr.s(auto_attribs=True, frozen=True)
class ChapterListing:
    stage: Stage
    name: str


@attr.s(auto_attribs=True, frozen=True)
class Text:
    category: int
    index: int
    name: str
    number_of_verses: int
    approximate_verses: bool
    chapters: Sequence[ChapterListing] = tuple()

    @property
    def id(self) -> TextId:
        return TextId(self.category, self.index)
