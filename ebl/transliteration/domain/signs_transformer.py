from lark import Token, Tree
from lark.visitors import Transformer, v_args

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import sub_index_to_int, to_sub_index
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


def tree_to_string(tree: Tree) -> str:
    _children = []
    for part in tree.scan_values(lambda x: x):
        if hasattr(part, "value"):
            _children.append(part.value)
        elif isinstance(part, Tree):
            _children.append(tree_to_string(part))
        else:
            _children.append(str(part))
    return "".join(_children)


class SignTransformer(Transformer):
    @v_args(inline=True)
    def ebl_atf_text_line__unidentified_sign(self, flags):
        return UnidentifiedSign.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__egyptian_metrical_feet_separator(self, flags):
        return EgyptianMetricalFeetSeparator.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unclear_sign(self, flags):
        return UnclearSign.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns.of()

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner.of(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args()
    def ebl_atf_text_line__value_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__logogram(self, name, sub_index, modifiers, flags, sign=None):
        return Logogram.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args(inline=True)
    def ebl_atf_text_line__surrogate(
        self, name, sub_index, modifiers, flags, surrogate
    ):
        return Logogram.of(
            tuple(name.children), sub_index, modifiers, flags, None, surrogate.children
        )

    @v_args()
    def ebl_atf_text_line__logogram_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__number(self, number, modifiers, flags, sign=None):
        return Number.of(tuple(number.children), modifiers, flags, sign)

    @v_args()
    def ebl_atf_text_line__number_name_head(self, children):
        return ValueToken.of("".join(children))

    @v_args()
    def ebl_atf_text_line__number_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, sub_index=""):
        return sub_index_to_int(sub_index)

    def ebl_atf_text_line__modifier(self, tokens):
        return "".join(map(str, tokens))

    def ebl_atf_text_line__modifiers(self, tokens):
        return tuple(map(str, tokens))

    def ebl_atf_text_line__flags(self, tokens):
        return tuple(map(atf.Flag, tokens))

    @v_args(inline=True)
    def ebl_atf_text_line__grapheme(self, name, sub_index, modifiers, flags):
        _name = tree_to_string(name)
        _sub_index = to_sub_index(sub_index) if sub_index and sub_index != 1 else ""
        return Grapheme.of(_name + _sub_index, modifiers, flags)

    def ebl_atf_text_line__sub_compound(self, children):
        return Tree("ebl_atf_text_line__sub_compound", ["(", *children, ")"])

    def ebl_atf_text_line__compound_grapheme(self, children):
        _children = []
        for part in children:
            if isinstance(part, Token):
                _children.append(part.value)
            elif isinstance(part, Tree):
                _children.append(tree_to_string(part))
            else:
                _children.append(str(part))
        return CompoundGrapheme.of(_children)
