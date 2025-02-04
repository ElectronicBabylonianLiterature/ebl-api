from lark.visitors import v_args
from ebl.transliteration.domain.translation_line_transformer import (
    TranslationLineTransformer,
)
from ebl.transliteration.domain.note_line_transformer import NoteLineTransformer
from ebl.transliteration.domain.parallel_line_transformer import ParallelLineTransformer
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.at_line_transformer import AtLineTransformer
from ebl.transliteration.domain.dollar_line_transformer import DollarLineTransformer
from ebl.transliteration.domain.line import ControlLine, EmptyLine


class LineTransformer(
    AtLineTransformer,
    DollarLineTransformer,
    NoteLineTransformer,
    TextLineTransformer,
    ParallelLineTransformer,
    TranslationLineTransformer,
):
    def __init__(self):
        super().__init__()

    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content):
        return ControlLine(prefix, content)
