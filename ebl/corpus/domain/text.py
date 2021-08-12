from typing import Sequence

import attr
import pydash

from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.translation_line import (
    DEFAULT_LANGUAGE,
    TranslationLine,
)


@attr.s(auto_attribs=True, frozen=True)
class ChapterListing:
    stage: Stage
    name: str
    translation: Sequence[TranslationLine]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return (
            pydash.chain(self.translation)
            .filter(lambda line: line.language == DEFAULT_LANGUAGE)
            .map(lambda line: line.parts)
            .head()
            .value()
            or tuple()
        )


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
