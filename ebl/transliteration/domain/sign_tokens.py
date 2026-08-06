from typing import Sequence

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.converters import convert_string_sequence
from ebl.transliteration.domain.named_signs import Logogram, Number, Reading
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_token_base import (
    AbstractSign,
    NamedSign,
    NameParts,
)
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    TokenVisitor,
    ValueToken,
)

__all__ = [
    "AbstractSign",
    "CompoundGrapheme",
    "Divider",
    "Grapheme",
    "Logogram",
    "NamedSign",
    "NameParts",
    "Number",
    "Reading",
]


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
    compound_parts: Sequence[str] = attr.ib(converter=convert_string_sequence)

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
