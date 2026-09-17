import re
from typing import Any, List, Optional, Sequence, cast
from lark import Tree
from lark.visitors import Transformer, v_args

from ebl.transliteration.domain.sign import SignName

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
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_token_base import NamedSignArguments
from ebl.transliteration.domain.tokens import (
    Token,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign


def name_arguments(
    tokens: Sequence[Token],
    sub_index: Optional[int] = 1,
    modifiers: Sequence[str] = (),
    flags: Sequence[atf.Flag] = (),
) -> NamedSignArguments:
    return NamedSignArguments(
        tuple(cast(Sequence[ValueToken], tokens[0::2])),
        sub_index,
        modifiers,
        flags,
        tuple(cast(Sequence[BrokenAway], tokens[1::2])),
    )


def tree_to_string(tree: Tree) -> str:
    return "".join(
        cast(Any, part).value if hasattr(part, "value") else str(part)
        for part in tree.scan_values(bool)
    )


class SignTransformer(Transformer):
    def __init__(self):
        super().__init__()
        for method in [method for method in dir(self) if "ebl_atf_text_line" in method]:
            setattr(self, f"ebl_atf_note_line__{method}", getattr(self, method))

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
    def ebl_atf_text_line__reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of_arguments(
            name_arguments(name.children, sub_index, modifiers, flags)
        ).with_sign(sign)

    @v_args()
    def ebl_atf_text_line__value_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__logogram(self, name, sub_index, modifiers, flags, sign=None):
        return Logogram.of_arguments(
            name_arguments(name.children, sub_index, modifiers, flags)
        ).with_sign(sign)

    @v_args(inline=True)
    def ebl_atf_text_line__surrogate(
        self, name, sub_index, modifiers, flags, surrogate
    ):
        return Logogram.of_arguments(
            name_arguments(name.children, sub_index, modifiers, flags)
        ).with_surrogate(surrogate.children)

    @v_args()
    def ebl_atf_text_line__logogram_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__number(self, number, modifiers, flags, sign=None):
        return Number.of_arguments(
            name_arguments(number.children, 1, modifiers, flags)
        ).with_sign(sign)

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
        return Grapheme.of(SignName(_name + _sub_index), modifiers, flags)

    def ebl_atf_text_line__sub_compound(self, children):
        return Tree("ebl_atf_text_line__sub_compound", ["(", *children, ")"])

    def ebl_atf_text_line__compound_grapheme(self, children):
        return CompoundGrapheme.of(self._parsed_graphemes_to_parts(children))

    def _parsed_graphemes_to_parts(self, children: Sequence) -> Sequence[str]:
        children = self._flatten_grapheme_elements(children)
        _children = []
        for index, part in enumerate(children):
            _children.append(str(part))
            if (
                index + 1 < len(children)
                and isinstance(part, Grapheme)
                and isinstance(children[index + 1], Grapheme)
            ):
                _children.append(".")
        return re.split(r"\.(?!(?:[^\(\)]*\)))", "".join(_children))

    def _flatten_grapheme_elements(self, children: Sequence) -> Sequence:
        _children: List[object] = []
        for part in children:
            if isinstance(part, Tree):
                _children += self._flatten_grapheme_elements(part.children)
            else:
                _children.append(part)
        return _children
