from typing import Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.translation_line import TranslationLine


@attr.s(auto_attribs=True, frozen=True)
class ChapterListing:
    stage: Stage
    name: str
    translation: Sequence[TranslationLine]


@attr.s(auto_attribs=True, frozen=True)
class Text:
    genre: Genre
    category: int
    index: int
    name: str
    number_of_verses: int
    approximate_verses: bool
    intro: str
    chapters: Sequence[ChapterListing] = tuple()
    references: Sequence[Reference] = tuple()

    @property
    def id(self) -> TextId:
        return TextId(self.genre, self.category, self.index)
