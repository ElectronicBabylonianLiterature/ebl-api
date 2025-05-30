from lark.visitors import v_args

from ebl.transliteration.domain.labels import LabelTransformer
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.note_line_transformer import MarkupTransformer
from ebl.transliteration.domain.translation_line import Extent, TranslationLine


class TranslationLineTransformer(LabelTransformer, MarkupTransformer):
    @v_args(inline=True)
    def translation_line(
        self, language, extent, *markup: MarkupPart
    ) -> TranslationLine:
        return TranslationLine(
            tuple(markup), language.value if language else "en", extent
        )

    @v_args(inline=True)
    def text_line__translation_extent(self, labels, line_number) -> Extent:
        return Extent(line_number, labels or ())
