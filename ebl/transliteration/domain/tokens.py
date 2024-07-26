from abc import ABC, abstractmethod
from enum import auto, Enum
from typing import AbstractSet, Optional, Sequence, Type, TypeVar

import attr

import ebl.transliteration.domain.atf as atf
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.language import Language


class TokenVisitor(ABC):  # noqa: B024
    def visit(self, token: "Token") -> None:  # noqa: B027
        pass

    def visit_word(self, word) -> None:
        self.visit(word)

    def visit_language_shift(self, shift) -> None:
        self.visit(shift)

    def visit_document_oriented_gloss(self, gloss) -> None:
        self.visit(gloss)

    def visit_broken_away(self, broken_away) -> None:
        self.visit(broken_away)

    def visit_perhaps_broken_away(self, broken_away) -> None:
        self.visit(broken_away)

    def visit_accidental_omission(self, omission) -> None:
        self.visit(omission)

    def visit_intentional_omission(self, omission) -> None:
        self.visit(omission)

    def visit_removal(self, removal) -> None:
        self.visit(removal)

    def visit_emendation(self, emendation) -> None:
        self.visit(emendation)

    def visit_erasure(self, erasure):
        self.visit(erasure)

    def visit_divider(self, divider) -> None:
        self.visit(divider)

    def visit_egyptian_metrical_feet_separator(
        self, egyptian_metrical_feet_separator
    ) -> None:
        self.visit(egyptian_metrical_feet_separator)

    def visit_line_break(self, line_break) -> None:
        self.visit(line_break)

    def visit_commentary_protocol(self, protocol) -> None:
        self.visit(protocol)

    def visit_variant(self, variant) -> None:
        self.visit(variant)

    def visit_gloss(self, gloss) -> None:
        self.visit(gloss)

    def visit_named_sign(self, named_sign) -> None:
        self.visit(named_sign)

    def visit_number(self, number) -> None:
        self.visit_named_sign(number)

    def visit_grapheme(self, grapheme) -> None:
        self.visit(grapheme)

    def visit_compound_grapheme(self, grapheme) -> None:
        self.visit(grapheme)

    def visit_unknown_sign(self, sign) -> None:
        self.visit(sign)

    def visit_akkadian_word(self, word) -> None:
        self.visit(word)

    def visit_greek_word(self, word) -> None:
        self.visit(word)

    def visit_metrical_foot_separator(self, separator) -> None:
        self.visit(separator)

    def visit_caesura(self, caesura) -> None:
        self.visit(caesura)

    @property
    def result(self) -> Sequence:
        return []

    _standardizations = []


class ErasureState(Enum):
    NONE = auto()
    ERASED = auto()
    OVER_ERASED = auto()


T = TypeVar("T", bound="Token")


@attr.s(frozen=True, auto_attribs=True)
class Token(ABC):
    enclosure_type: AbstractSet[EnclosureType]
    erasure: ErasureState

    @property
    @abstractmethod
    def value(self) -> str: ...

    @property
    @abstractmethod
    def parts(self) -> Sequence["Token"]: ...

    @property
    def clean_value(self) -> str:
        return self.value

    @property
    def lemmatizable(self) -> bool:
        return False

    @property
    def alignable(self) -> bool:
        return self.lemmatizable

    def get_key(self) -> str:
        parts = (
            f"⟨{'⁚'.join(part.get_key() for part in self.parts)}⟩" if self.parts else ""
        )
        return f"{type(self).__name__}⁝{self.value}{parts}"

    def set_unique_lemma(self: T, lemma: LemmatizationToken) -> T:
        if lemma.unique_lemma is None and lemma.value == self.value:
            return self
        else:
            raise LemmatizationError(
                f"Incompatible lemmatization token {lemma} for {self}"
            )

    def update_alignment(self: T, alignment_map) -> T:
        return self

    def set_enclosure_type(self: T, enclosure_type: AbstractSet[EnclosureType]) -> T:
        return attr.evolve(self, enclosure_type=enclosure_type)

    def set_erasure(self: T, erasure: ErasureState) -> T:
        return attr.evolve(self, erasure=erasure)

    def merge(self, token: T) -> T:
        return token

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit(self)


VT = TypeVar("VT", bound="ValueToken")


@attr.s(auto_attribs=True, frozen=True)
class ValueToken(Token):
    _value: str

    @property
    def value(self) -> str:
        return self._value

    @property
    def parts(self):
        return tuple()

    @classmethod
    def of(cls: Type[VT], value: str) -> VT:
        return cls(frozenset(), ErasureState.NONE, value)


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
        return tuple()

    @staticmethod
    def of() -> "UnknownNumberOfSigns":
        return UnknownNumberOfSigns(frozenset(), ErasureState.NONE)


@attr.s(frozen=True)
class Tabulation(Token):
    @property
    def value(self) -> str:
        return atf.TABULATION

    @property
    def parts(self):
        return tuple()

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


@attr.s(frozen=True, auto_attribs=True)
class Column(Token):
    number: Optional[int] = attr.ib(default=None)

    @staticmethod
    def of(number: Optional[int] = None) -> "Column":
        return Column(frozenset(), ErasureState.NONE, number)

    @number.validator
    def _check_number(self, _, value) -> None:
        if value is not None and value < 0:
            raise ValueError("number must not be negative")

    @property
    def value(self) -> str:
        return "&" if self.number is None else f"&{self.number}"

    @property
    def parts(self):
        return tuple()


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
        return tuple()

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
        return tuple()

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit_line_break(self)

    @staticmethod
    def of() -> "LineBreak":
        return LineBreak(frozenset(), ErasureState.NONE)
