from lark.visitors import Transformer, v_args

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import sub_index_to_int
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Grapheme,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.tokens import UnknownNumberOfSigns, ValueToken
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign


class SignTransformer(Transformer):
    @v_args(inline=True)
    def text_line__text__unidentified_sign(self, flags):
        return UnidentifiedSign.of(flags)

    @v_args(inline=True)
    def text_line__text__egyptian_metrical_feet_separator(self, flags):
        return EgyptianMetricalFeetSeparator.of(flags)

    @v_args(inline=True)
    def text_line__text__unclear_sign(self, flags):
        return UnclearSign.of(flags)

    @v_args(inline=True)
    def text_line__text__unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns.of()

    @v_args(inline=True)
    def text_line__text__joiner(self, symbol):
        return Joiner.of(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def text_line__text__reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args()
    def text_line__text__value_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def text_line__text__logogram(self, name, sub_index, modifiers, flags, sign=None):
        return Logogram.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args(inline=True)
    def text_line__text__surrogate(self, name, sub_index, modifiers, flags, surrogate):
        return Logogram.of(
            tuple(name.children), sub_index, modifiers, flags, None, surrogate.children
        )

    @v_args()
    def text_line__text__logogram_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def text_line__text__number(self, number, modifiers, flags, sign=None):
        return Number.of(tuple(number.children), modifiers, flags, sign)

    @v_args()
    def text_line__text__number_name_head(self, children):
        return ValueToken.of("".join(children))

    @v_args()
    def text_line__text__number_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def text_line__text__sub_index(self, sub_index=""):
        return sub_index_to_int(sub_index)

    def text_line__text__modifiers(self, tokens):
        return tuple(map(str, tokens))

    def text_line__text__flags(self, tokens):
        return tuple(map(atf.Flag, tokens))

    @v_args(inline=True)
    def text_line__text__grapheme(self, name, modifiers, flags):
        return Grapheme.of(name.value, modifiers, flags)

    def text_line__text__compound_grapheme(self, children):
        return CompoundGrapheme.of([part.value for part in children])
