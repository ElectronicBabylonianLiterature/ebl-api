from typing import Iterable

from lark.visitors import v_args
from ebl.common.domain.period import Period

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    Siglum,
)
from ebl.corpus.domain.provenance import Provenance
from ebl.transliteration.domain.line_transformer import LineTransformer


class ChapterTransformer(LineTransformer):
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
