from typing import Optional, Sequence, Union

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import to_sub_index
from ebl.transliteration.domain.converters import (
    convert_flag_sequence,
    convert_string_sequence,
    convert_token_sequence,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.tokens import Token, TokenVisitor, ValueToken


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    modifiers: Sequence[str] = attr.ib(converter=convert_string_sequence)
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]


NameParts = Sequence[Union[ValueToken, BrokenAway]]


@attr.s(auto_attribs=True, frozen=True)
class NamedSign(AbstractSign):
    name_parts: NameParts = attr.ib(converter=convert_token_sequence)
    sub_index: Optional[int] = attr.ib(default=1)
    sign: Optional[Token] = None

    @sub_index.validator
    def _check_sub_index(self, _attribute, value):
        if value is not None and value < 0:
            raise ValueError("Sub-index must be >= 0.")

    @property
    def name(self) -> str:
        return "".join(
            token.value for token in self.name_parts if isinstance(token, ValueToken)
        )

    @property
    def clean_value(self) -> str:
        sub_index = to_sub_index(self.sub_index)
        modifiers = "".join(self.modifiers)
        sign = f"({self.sign.value})" if self.sign else ""
        return f"{self.name}{sub_index}{modifiers}{sign}"

    @property
    def parts(self) -> Sequence[Token]:
        if self.sign:
            return (*self.name_parts, self.sign)
        else:
            return self.name_parts

    @property
    def value(self) -> str:
        name = "".join(token.value for token in self.name_parts)
        sub_index = to_sub_index(self.sub_index)
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        sign = f"({self.sign.value})" if self.sign else ""
        return f"{name}{sub_index}{modifiers}{flags}{sign}"

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_named_sign(self)
