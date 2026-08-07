from typing import Optional, Sequence

import attr

import ebl.transliteration.domain.atf as atf
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.token_base import (
    ErasureState,
    SignsCollectingVisitor,
    Token,
    TokenVisitor,
    ValueToken,
)

__all__ = [
    "Column",
    "CommentaryProtocol",
    "ErasureState",
    "Joiner",
    "LanguageShift",
    "LineBreak",
    "SignsCollectingVisitor",
    "Tabulation",
    "Token",
    "TokenVisitor",
    "UnknownNumberOfSigns",
    "WordOmitted",
    "ValueToken",
    "Variant",
]


@attr.s(frozen=True)
class LanguageShift(ValueToken):
    _normalization_shift = "%n"

    @property
    def language(self):
        return Language.of_atf(self.value)

    @property
    def normalized(self):
        return self.value == LanguageShift._normalization_shift

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit_language_shift(self)

    @staticmethod
    def normalized_akkadian():
        return LanguageShift.of(LanguageShift._normalization_shift)


@attr.s(frozen=True)
class UnknownNumberOfSigns(Token):
    @property
    def value(self) -> str:
        return atf.UNKNOWN_NUMBER_OF_SIGNS

    @property
    def parts(self):
        return ()

    @staticmethod
    def of() -> "UnknownNumberOfSigns":
        return UnknownNumberOfSigns(frozenset(), ErasureState.NONE)


@attr.s(frozen=True)
class WordOmitted(Token):
    @property
    def value(self) -> str:
        return atf.WORD_OMITTED

    @property
    def parts(self):
        return ()

    @staticmethod
    def of() -> "WordOmitted":
        return WordOmitted(frozenset(), ErasureState.NONE)


@attr.s(frozen=True)
class Tabulation(Token):
    @property
    def value(self) -> str:
        return atf.TABULATION

    @property
    def parts(self):
        return ()

    @staticmethod
    def of() -> "Tabulation":
        return Tabulation(frozenset(), ErasureState.NONE)


@attr.s(frozen=True)
class CommentaryProtocol(ValueToken):
    @property
    def protocol(self):
        return atf.CommentaryProtocol(self.value)

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit_commentary_protocol(self)


def _validate_column_number(_instance, _attribute, value: Optional[int]) -> None:
    if value is not None and value < 0:
        raise ValueError("number must not be negative")


@attr.s(frozen=True, auto_attribs=True)
class Column(Token):
    number: Optional[int] = attr.ib(default=None, validator=_validate_column_number)

    @staticmethod
    def of(number: Optional[int] = None) -> "Column":
        return Column(frozenset(), ErasureState.NONE, number)

    @property
    def value(self) -> str:
        return "&" if self.number is None else f"&{self.number}"

    @property
    def parts(self):
        return ()


@attr.s(frozen=True, auto_attribs=True)
class Variant(Token):
    tokens: Sequence[Token]

    @staticmethod
    def of(*args: Token) -> "Variant":
        return Variant(frozenset(), ErasureState.NONE, tuple(args))

    @property
    def value(self) -> str:
        return atf.VARIANT_SEPARATOR.join(token.value for token in self.tokens)

    @property
    def clean_value(self) -> str:
        return atf.VARIANT_SEPARATOR.join(token.clean_value for token in self.tokens)

    @property
    def parts(self):
        return self.tokens

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit_variant(self)


@attr.s(auto_attribs=True, frozen=True)
class Joiner(Token):
    _value: atf.Joiner

    @property
    def value(self):
        return self._value.value

    @property
    def parts(self):
        return ()

    @staticmethod
    def dot():
        return Joiner.of(atf.Joiner.DOT)

    @staticmethod
    def hyphen():
        return Joiner.of(atf.Joiner.HYPHEN)

    @staticmethod
    def colon():
        return Joiner.of(atf.Joiner.COLON)

    @staticmethod
    def semicolon():
        return Joiner.of(atf.Joiner.SEMICOLON)

    @staticmethod
    def plus():
        return Joiner.of(atf.Joiner.PLUS)

    @staticmethod
    def comma():
        return Joiner.of(atf.Joiner.PLUS)

    @staticmethod
    def of(joiner: atf.Joiner):
        return Joiner(frozenset(), ErasureState.NONE, joiner)


@attr.s(frozen=True, auto_attribs=True)
class LineBreak(Token):
    @property
    def value(self) -> str:
        return atf.LINE_BREAK

    @property
    def parts(self):
        return ()

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit_line_break(self)

    @staticmethod
    def of() -> "LineBreak":
        return LineBreak(frozenset(), ErasureState.NONE)
