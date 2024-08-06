from typing import Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.chapter import make_title
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class UncertainFragment:
    museum_number: MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class ChapterListing:
    stage: Stage
    name: str
    translation: Sequence[TranslationLine]
    uncertain_fragments: Sequence[UncertainFragment]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return make_title(self.translation)


@attr.s(auto_attribs=True, frozen=True)
class Text:
    genre: Genre
    category: int
    index: int
    name: str
    has_doi: bool
    number_of_verses: int
    approximate_verses: bool
    intro: str
    chapters: Sequence[ChapterListing] = ()
    references: Sequence[Reference] = ()
    projects: Sequence[str] = ()

    @property
    def id(self) -> TextId:
        return TextId(self.genre, self.category, self.index)

    @property
    def has_multiple_stages(self) -> bool:
        return len({chapter.stage for chapter in self.chapters}) > 1
