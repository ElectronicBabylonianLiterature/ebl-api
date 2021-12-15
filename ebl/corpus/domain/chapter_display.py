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
from ebl.transliteration.domain.markup import MarkupPart, to_title


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
    intertext: Sequence[MarkupPart]
    reconstruction: Sequence[Token]
    translation: Sequence[MarkupPart]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return to_title(self.translation)

    @staticmethod
    def of_line(line: Line) -> "LineDisplay":
        return LineDisplay(
            line.number,
            line.variants[0].intertext,
            line.variants[0].reconstruction,
            get_default_translation(line.translation),
        )


@attr.s(frozen=True, auto_attribs=True)
class ChapterDisplay:
    id_: ChapterId
    text_name: str
    is_single_stage: bool
    lines: Sequence[LineDisplay]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return self.lines[0].title if self.lines else tuple()

    @staticmethod
    def of_chapter(text: Text, chapter: Chapter) -> "ChapterDisplay":
        return ChapterDisplay(
            chapter.id_,
            text.name,
            not text.has_multiple_stages,
            tuple(map(LineDisplay.of_line, chapter.lines)),
        )
