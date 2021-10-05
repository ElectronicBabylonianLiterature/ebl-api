from typing import Iterable

from lark.visitors import v_args

from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import (
    Manuscript,
    Period,
    Provenance,
    ManuscriptType,
    Siglum,
)
from ebl.transliteration.domain.dollar_line_transformer import DollarLineTransfomer
from ebl.transliteration.domain.labels import LabelTransformer
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.note_line_transformer import NoteLineTransformer
from ebl.transliteration.domain.parallel_line_transformer import ParallelLineTransformer
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.translation_line_transformer import (
    TranslationLineTransformer,
)


class ChapterTransformer(
    DollarLineTransfomer,
    NoteLineTransformer,
    TextLineTransformer,
    TranslationLineTransformer,
    ParallelLineTransformer,
    LabelTransformer,
):
    def __init__(self, manuscripts: Iterable[Manuscript]):
        self._manuscripts = {
            manuscript.siglum: manuscript.id for manuscript in manuscripts
        }

    def manuscript_label(self, children):
        return children

    @v_args(inline=True)
    def siglum(self, provenance, period, type_, disambiquator):
        return Siglum(
            Provenance.from_abbreviation(provenance or ""),
            Period.from_abbreviation(period),
            ManuscriptType.from_abbreviation(type_ or ""),
            disambiquator or "",
        )

    @v_args(inline=True)
    def standard_text_siglum(self, disambiquator):
        return Siglum(
            Provenance.STANDARD_TEXT,
            Period.NONE,
            ManuscriptType.NONE,
            disambiquator or "",
        )

    @v_args(inline=True)
    def manuscript_line(self, siglum, labels, line, *paratext):
        return ManuscriptLine(
            self._manuscripts[siglum], labels or tuple(), line, tuple(paratext)
        )

    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def reconstruction(self, line, note, *parallels):
        return (line, note, tuple(parallels))

    @v_args(inline=True)
    def line_variant(self, reconstruction, *manuscripts):
        text_line, notes, parallel_lines = reconstruction
        return (
            text_line.line_number,
            LineVariant(text_line.content, notes, tuple(manuscripts), parallel_lines),
        )

    def chapter_translation(self, lines):
        return tuple(lines)

    @v_args(inline=True)
    def chapter_line(self, translation, head, *tail):
        line_number, main_variant = head
        return Line(
            line_number,
            (main_variant, *[variant for _, variant in tail]),
            translation=translation or tuple(),
        )

    def chapter(self, lines):
        return tuple(lines)
