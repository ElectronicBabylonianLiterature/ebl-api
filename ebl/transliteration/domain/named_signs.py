from typing import Optional, Sequence

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.converters import convert_token_sequence
from ebl.transliteration.domain.sign_token_base import NamedSign, convert_name_parts
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    TokenVisitor,
    ValueToken,
)


@attr.s(auto_attribs=True, frozen=True)
class Reading(NamedSign):
    @staticmethod
    def of(
        name: Sequence[Token],
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> "Reading":
        return Reading(
            frozenset(),
            ErasureState.NONE,
            modifiers,
            flags,
            convert_name_parts(name),
            sub_index,
            sign,
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

    def with_surrogate(self, surrogate: Sequence[Token]) -> "Logogram":
        return attr.evolve(self, surrogate=surrogate)

    @staticmethod
    def of(
        name: Sequence[Token],
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> "Logogram":
        return Logogram(
            frozenset(),
            ErasureState.NONE,
            modifiers,
            flags,
            convert_name_parts(name),
            sub_index,
            sign,
        )

    @staticmethod
    def of_name(
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> "Logogram":
        return Logogram.of((ValueToken.of(name),), sub_index, modifiers, flags, sign)


@attr.s(auto_attribs=True, frozen=True)
class Number(NamedSign):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_number(self)

    @staticmethod
    def of(
        name: Sequence[Token],
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
        sub_index: int = 1,
    ) -> "Number":
        return Number(
            frozenset(),
            ErasureState.NONE,
            modifiers,
            flags,
            convert_name_parts(name),
            sub_index,
            sign,
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
