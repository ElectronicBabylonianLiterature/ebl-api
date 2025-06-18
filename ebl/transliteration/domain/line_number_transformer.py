from lark.visitors import Transformer, v_args

from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange


class LineNumberTransformer(Transformer):
    @v_args(inline=True)
    def line_number_range(self, start, end):
        return LineNumberRange(start, end)

    @v_args(inline=True)
    def single_line_number(self, prefix_modifier, number, prime, suffix_modifier):
        return LineNumber(
            int(number), prime is not None, prefix_modifier, suffix_modifier
        )
