from typing import Sequence

import attr

from ebl.corpus.domain.chapter import ChapterId, Chapter
from ebl.corpus.domain.line import Line, LineVariant
from ebl.corpus.domain.record import Record
from ebl.corpus.domain.text import Text
from ebl.transliteration.domain.translation_line import (
    DEFAULT_LANGUAGE,
    TranslationLine,
)
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.markup import MarkupPart, to_title


def get_default_translation(
    translations: Sequence[TranslationLine],
) -> Sequence[MarkupPart]:
    return next(
        (
            translation_line.parts
            for translation_line in translations
            if translation_line.language == DEFAULT_LANGUAGE
        ),
        tuple(),
    )


@attr.s(frozen=True, auto_attribs=True)
class LineDisplay:
    number: AbstractLineNumber
    is_second_line_of_parallelism: bool
    is_beginning_of_section: bool
    variants: Sequence[LineVariant]
    translation: Sequence[TranslationLine]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return to_title(get_default_translation(self.translation))
    
    @staticmethod
    def of_line(line: Line) -> "LineDisplay":
        return LineDisplay(
            line.number,
            line.is_second_line_of_parallelism,
            line.is_beginning_of_section,
            line.variants,
            line.translation,
        )


@attr.s(frozen=True, auto_attribs=True)
class ChapterDisplay:
    id_: ChapterId
    text_name: str
    text_has_doi: bool
    is_single_stage: bool
    lines: Sequence[LineDisplay]
    record: Record
    atf: str

    @property
    def title(self) -> Sequence[MarkupPart]:
        return self.lines[0].title if self.lines else tuple()

    @staticmethod
    def of_chapter(text: Text, chapter: Chapter) -> "ChapterDisplay":
        return ChapterDisplay(
            chapter.id_,
            text.name,
            text.has_doi,
            not text.has_multiple_stages,
            tuple(map(LineDisplay.of_line, chapter.lines)),
            chapter.record,
            chapter.atf
        )
