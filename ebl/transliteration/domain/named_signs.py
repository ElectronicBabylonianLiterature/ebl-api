from typing import Sequence

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.converters import convert_token_sequence
from ebl.transliteration.domain.sign_token_base import (
    NamedSign,
    NamedSignArguments,
    NamedSignWithLeadingSubIndex,
)
from ebl.transliteration.domain.tokens import Token, TokenVisitor, ValueToken


@attr.s(auto_attribs=True, frozen=True)
class Reading(NamedSignWithLeadingSubIndex):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Logogram(NamedSignWithLeadingSubIndex):
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


@attr.s(auto_attribs=True, frozen=True)
class Number(NamedSign):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_number(self)

    @staticmethod
    def of(
        name: Sequence[Token],
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sub_index: int = 1,
    ) -> "Number":
        return Number._create(NamedSignArguments(name, sub_index, modifiers, flags))

    @staticmethod
    def of_name(
        name: str,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sub_index: int = 1,
    ) -> "Number":
        return Number.of((ValueToken.of(name),), modifiers, flags, sub_index)
