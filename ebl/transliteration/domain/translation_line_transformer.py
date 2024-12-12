from lark.visitors import v_args

from ebl.transliteration.domain.labels import LabelTransformer
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.note_line_transformer import MarkupTransformer
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.line_number import (
    LineNumber,
)


class TranslationLineTransformer(LabelTransformer, MarkupTransformer):
    def __init__(self):
        super(LabelTransformer, self).__init__()
        super(MarkupTransformer, self).__init__()

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
        print(labels, line_number)
        input()
        # ToDo: continue from here
        # translation-expected_line4] (Tree('ebl_atf_translation_line__ebl_atf_common__surface_label',
        # [Token('ebl_atf_translation_line__ebl_atf_common__OBVERSE', 'o'), Tree('ebl_atf_translation_line__ebl_atf_common__status', [])]),
        # Tree('ebl_atf_translation_line__ebl_atf_common__column_label', [Token('ebl_atf_translation_line__ebl_atf_common__ROMAN_NUMERAL', 'iii'),
        # Tree('ebl_atf_translation_line__ebl_atf_common__status', [])])) LineNumber(number=1, has_prime=False, prefix_modifier=None, suffix_modifier=None)
        return Extent(line_number, labels or ())

    @v_args(inline=True)
    def ebl_atf_translation_line__ebl_atf_common__single_line_number(
        self, prefix_modifier, number, prime, suffix_modifier
    ):
        return LineNumber(
            int(number), prime is not None, prefix_modifier, suffix_modifier
        )
