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
        # ToDo: Fix the following issue in
        # `ebl/tests/atf_importer/test_atf_importer.py::test_atf_importer`
        #
        """
        Converting: "AD-651.atf"
        E               lark.exceptions.VisitError: Error trying to process rule "ebl_atf_translation_line__translation_extent":
        E
        E               ebl_atf_translation_line__translation_extent() missing 2 required positional arguments: 'labels' and 'line_number'
        """
        return Extent(line_number, labels or ())
