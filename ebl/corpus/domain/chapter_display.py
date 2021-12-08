from typing import Iterable, Sequence
import attr

from ebl.corpus.domain.chapter import ChapterId, Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.text import Text
from ebl.transliteration.domain.translation_line import (
    DEFAULT_LANGUAGE,
    TranslationLine,
)
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.markup import MarkupPart


def get_default_translation(
    translations: Iterable[TranslationLine],
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
    reconstruction: Sequence[Token]
    translation: Sequence[MarkupPart]

    @staticmethod
    def of_line(line: Line) -> "LineDisplay":
        return LineDisplay(
            line.number,
            line.variants[0].reconstruction,
            get_default_translation(line.translation),
        )


@attr.s(frozen=True, auto_attribs=True)
class ChapterDisplay:
    id_: ChapterId
    text_name: str
    lines: Sequence[LineDisplay]

    @staticmethod
    def of_chapter(text: Text, chapter: Chapter) -> "ChapterDisplay":
        return ChapterDisplay(
            chapter.id_,
            text.name,
            tuple(map(LineDisplay.of_line, chapter.lines)),
        )
