from lark.visitors import v_args

from ebl.corpus.domain.manuscript import Period, Provenance, ManuscriptType, Siglum
from ebl.corpus.domain.chapter import ManuscriptLine
from ebl.transliteration.domain.dollar_line_transformer import DollarLineTransfomer
from ebl.transliteration.domain.note_line_transformer import NoteLineTransformer
from ebl.transliteration.domain.parallel_line_transformer import ParallelLineTransformer
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.labels import LabelTransformer
from ebl.transliteration.domain.line import EmptyLine


class ChapterTransformer(
    DollarLineTransfomer,
    NoteLineTransformer,
    TextLineTransformer,
    ParallelLineTransformer,
    LabelTransformer,
):
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
    def manuscript_line(self, siglum, labels, line, *paratext):
        return ManuscriptLine(0, labels or tuple(), line, tuple(paratext))

    def empty_line(self, _):
        return EmptyLine()
