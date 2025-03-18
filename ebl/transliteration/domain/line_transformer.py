from lark.visitors import v_args, VisitError
from ebl.transliteration.domain.translation_line_transformer import (
    TranslationLineTransformer,
)
from ebl.transliteration.domain.note_line_transformer import NoteLineTransformer
from ebl.transliteration.domain.parallel_line_transformer import ParallelLineTransformer
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.at_line_transformer import AtLineTransformer
from ebl.transliteration.domain.dollar_line_transformer import DollarLineTransformer
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from lark.exceptions import ParseError


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

    def transform(self, tree):
        try:
            return super().transform(tree)
        except VisitError as error:
            if isinstance(error.orig_exc, ParseError):
                raise error.orig_exc
            else:
                raise

    def empty_line(self, _) -> EmptyLine:
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content) -> ControlLine:
        return ControlLine(prefix, content)

    @v_args(inline=True)
    def ebl_atf_translation_line__legacy_translation_block_line(self, *args) -> None:
        raise ParseError
