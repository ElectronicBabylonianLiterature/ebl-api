from lark.visitors import v_args
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.note_line_transformer import MarkupTransformer
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.common_transformer import CommonTransformer


class TranslationLineTransformer(CommonTransformer, MarkupTransformer):
    def __init__(self):
        super().__init__()

    @v_args(inline=True)
    def translation_line(
        self, language, extent, *markup: MarkupPart
    ) -> TranslationLine:
        return TranslationLine(
            tuple(markup), language.value if language else "en", extent
        )

    @v_args(inline=True)
    def ebl_atf_translation_line__translation_extent(
        self, labels, line_number
    ) -> Extent:
        return Extent(line_number, labels or ())
