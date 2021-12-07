from typing import Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.chapter import get_title
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class UncertainFragment:
    museum_number: MuseumNumber
    is_in_fragmentarium: bool


@attr.s(auto_attribs=True, frozen=True)
class ChapterListing:
    stage: Stage
    name: str
    translation: Sequence[TranslationLine]
    uncertain_fragments: Sequence[UncertainFragment]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return get_title(self.translation)


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
