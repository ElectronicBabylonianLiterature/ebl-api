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
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    ValueToken,
    TokenVisitor,
)


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    modifiers: Sequence[str] = attr.ib(converter=convert_string_sequence)
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]


@attr.s(frozen=True, auto_attribs=True)
class Divider(AbstractSign):
    divider: str

    @property
    def value(self) -> str:
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        return f"{self.divider}{modifiers}{flags}"

    @property
    def parts(self):
        return ()

    @property
    def clean_value(self) -> str:
        modifiers = "".join(self.modifiers)
        return f"{self.divider}{modifiers}"

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_divider(self)

    @staticmethod
    def of(
        divider: str,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
    ):
        return Divider(frozenset(), ErasureState.NONE, modifiers, flags, divider)


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


@attr.s(auto_attribs=True, frozen=True)
class Reading(NamedSign):
    @staticmethod
    def of(
        name: NameParts,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> "Reading":
        return Reading(
            frozenset(), ErasureState.NONE, modifiers, flags, name, sub_index, sign
        )

    @staticmethod
    def of_name(
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> "Reading":
        return Reading.of((ValueToken.of(name),), sub_index, modifiers, flags, sign)


@attr.s(auto_attribs=True, frozen=True)
class Logogram(NamedSign):
    surrogate: Sequence[Token] = attr.ib(default=(), converter=convert_token_sequence)

    @property
    def value(self) -> str:
        return f"{super().value}{self._surrogate_value}"

    @property
    def clean_value(self) -> str:
        return f"{super().clean_value}{self._surrogate_value}"

    @property
    def _surrogate_value(self) -> str:
        return (
            f"<({''.join(token.value for token in self.surrogate)})>"
            if self.surrogate
            else ""
        )

    @staticmethod
    def of(
        name: NameParts,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
        surrogate: Sequence[Token] = (),
    ) -> "Logogram":
        return Logogram(
            frozenset(),
            ErasureState.NONE,
            modifiers,
            flags,
            name,
            sub_index,
            sign,
            surrogate,
        )

    @staticmethod
    def of_name(
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
        surrogate: Sequence[Token] = (),
    ) -> "Logogram":
        return Logogram.of(
            (ValueToken.of(name),), sub_index, modifiers, flags, sign, surrogate
        )


@attr.s(auto_attribs=True, frozen=True)
class Number(NamedSign):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_number(self)

    @staticmethod
    def of(
        name: NameParts,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
        sub_index: int = 1,
    ) -> "Number":
        return Number(
            frozenset(), ErasureState.NONE, modifiers, flags, name, sub_index, sign
        )

    @staticmethod
    def of_name(
        name: str,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
        sub_index: int = 1,
    ) -> "Number":
        return Number.of((ValueToken.of(name),), modifiers, flags, sign, sub_index)


@attr.s(auto_attribs=True, frozen=True)
class Grapheme(AbstractSign):
    name: SignName

    def __str__(self) -> str:
        return self.value

    @property
    def value(self) -> str:
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        return f"{self.name}{modifiers}{flags}"

    @property
    def clean_value(self) -> str:
        modifiers = "".join(self.modifiers)
        return f"{self.name}{modifiers}"

    @property
    def parts(self):
        return ()

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_grapheme(self)

    @staticmethod
    def of(
        name: SignName,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
    ) -> "Grapheme":
        return Grapheme(frozenset(), ErasureState.NONE, modifiers, flags, name)


@attr.s(auto_attribs=True, frozen=True)
class CompoundGrapheme(Token):
    compound_parts: Sequence[str] = attr.ib(converter=convert_token_sequence)

    @property
    def name(self) -> SignName:
        parts = ".".join(self.compound_parts)
        delimiter = atf.COMPOUND_GRAPHEME_DELIMITER
        return SignName(f"{delimiter}{parts}{delimiter}")

    @property
    def value(self) -> str:
        return self.name

    @property
    def parts(self) -> Sequence[Token]:
        return [ValueToken.of(part) for part in self.compound_parts]

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_compound_grapheme(self)

    @staticmethod
    def of(parts: Sequence[str]) -> "CompoundGrapheme":
        return CompoundGrapheme(frozenset(), ErasureState.NONE, parts)
