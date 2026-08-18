from abc import ABC, abstractmethod
from enum import auto, Enum
from typing import AbstractSet, Sequence, Type, TypeVar

import attr

from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType


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


class SignsCollectingVisitor(TokenVisitor, ABC):
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def result_string(self) -> Sequence[str]:
        raise NotImplementedError


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
    def value(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def parts(self) -> Sequence["Token"]:
        raise NotImplementedError

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
        return ()

    @classmethod
    def of(cls: Type[VT], value: str) -> VT:
        return cls(frozenset(), ErasureState.NONE, value)
