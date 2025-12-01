from typing import Sequence, Callable

import attr

from ebl.corpus.domain.chapter import ChapterId, Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.record import Record
from ebl.corpus.domain.text import Text
from ebl.transliteration.domain.translation_line import (
    DEFAULT_LANGUAGE,
    TranslationLine,
)
from ebl.transliteration.domain.line_number import AbstractLineNumber, OldLineNumber
from ebl.transliteration.domain.markup import MarkupPart, to_title
from ebl.corpus.domain.manuscript import Manuscript
import ebl.corpus.domain.chapter_validators as validators
from ebl.errors import NotFoundError
from ebl.transliteration.domain.atf import Atf


def get_default_translation(
    translations: Sequence[TranslationLine],
) -> Sequence[MarkupPart]:
    return next(
        (
            translation_line.parts
            for translation_line in translations
            if translation_line.language == DEFAULT_LANGUAGE
        ),
        (),
    )


@attr.s(frozen=True, auto_attribs=True)
class LineDisplay:
    number: AbstractLineNumber
    old_line_numbers: Sequence[OldLineNumber]
    is_second_line_of_parallelism: bool
    is_beginning_of_section: bool
    variants: Sequence[LineVariant]
    translation: Sequence[TranslationLine]

    @property
    def title(self) -> Sequence[MarkupPart]:
        return to_title(get_default_translation(self.translation))

    def get_atf(self, get_manuscript: Callable[[int], Manuscript]) -> Atf:
        line_atf_blocks = []
        for index, variant in enumerate(self.variants):
            reconstruction = f"{self.number.atf} {variant.reconstruction_atf}"
            reconstruction_note = variant.note.atf if variant.note else ""
            translation = (
                self.translation[index].atf if len(self.translation) > index else ""
            )
            atf_blocks = [
                translation,
                reconstruction,
                variant.note_atf,
                reconstruction_note,
                variant.parallels_atf,
                variant.get_manuscript_lines_atf(get_manuscript),
            ]
            line_atf_blocks.append(
                "\n".join(atf_block for atf_block in atf_blocks if atf_block)
            )
        return Atf("\n\n".join(line_atf_blocks))

    @staticmethod
    def of_line(line: Line) -> "LineDisplay":
        return LineDisplay(
            line.number,
            line.old_line_numbers,
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
    manuscripts: Sequence[Manuscript] = attr.ib(
        default=(),
        validator=[
            validators.validate_manuscript_ids,
            validators.validate_manuscript_sigla,
        ],
    )

    @property
    def title(self) -> Sequence[MarkupPart]:
        return self.lines[0].title if self.lines else ()

    @property
    def atf(self) -> Atf:
        atf_name = (
            f"{self.id_.text_id} {self.text_name} "
            f"{self.id_.stage.abbreviation} {self.id_.name}"
        )
        atf_header = f"&X000001 = {atf_name}"
        atf_meta = "\n".join(
            [atf_header, "#project: eblo"]
            + [
                f"#atf: {declaration}"
                for declaration in [
                    "lang akk-x-stdbab",
                    "use unicode",
                    "use math",
                    "use legacy",
                ]
            ]
        )
        return Atf(
            "\n\n".join(
                [atf_meta] + [line.get_atf(self.get_manuscript) for line in self.lines]
            )
        )

    def get_manuscript(self, id_: int) -> Manuscript:
        try:
            return next(
                manuscript for manuscript in self.manuscripts if manuscript.id == id_
            )
        except StopIteration as error:
            raise NotFoundError(f"No manuscripts with id {id_}.") from error

    @staticmethod
    def of_chapter(text: Text, chapter: Chapter) -> "ChapterDisplay":
        return ChapterDisplay(
            chapter.id_,
            text.name,
            text.has_doi,
            not text.has_multiple_stages,
            tuple(map(LineDisplay.of_line, chapter.lines)),
            chapter.record,
            chapter.manuscripts,
        )
