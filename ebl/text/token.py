import collections
from enum import Enum, auto
from typing import Any, NewType, Tuple

import attr

import ebl.text.atf
from ebl.text.language import Language
from ebl.text.lemmatization import LemmatizationError, LemmatizationToken

DEFAULT_LANGUAGE = Language.AKKADIAN
DEFAULT_NORMALIZED = False
UniqueLemma = NewType('UniqueLemma', str)
Partial = collections.namedtuple('Partial', 'start end')


class Side(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


@attr.s(auto_attribs=True, frozen=True)
class Token:
    value: str

    @property
    def lemmatizable(self) -> bool:
        return False

    def set_unique_lemma(
            self,
            lemma: LemmatizationToken
    ) -> 'Token':
        if lemma.unique_lemma is None and lemma.value == self.value:
            return self
        else:
            raise LemmatizationError()

    def accept(self, visitor: Any) -> None:
        visitor.visit_token(self)

    def to_dict(self) -> dict:
        return {
            'type': 'Token',
            'value': self.value
        }


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Tuple[UniqueLemma, ...] = tuple()

    @property
    def lemmatizable(self) -> bool:
        non_lemmatizable_chars = [
            ebl.text.atf.VARIANT_SEPARATOR,
            ebl.text.atf.UNCLEAR_SIGN,
            ebl.text.atf.UNIDENTIFIED_SIGN
        ]
        return (
            self.language.lemmatizable and
            not self.normalized and
            all((char not in self.value)
                for char
                in non_lemmatizable_chars) and
            not any(self.partial)
        )

    @property
    def partial(self) -> Partial:
        return Partial(
            any(
                self.value.startswith(joiner)
                for joiner
                in ebl.text.atf.JOINERS
            ),
            any(
                self.value.endswith(joiner)
                for joiner
                in ebl.text.atf.JOINERS
            )
        )

    def set_language(self, language: Language, normalized: bool) -> 'Word':
        return attr.evolve(self, language=language, normalized=normalized)

    def set_unique_lemma(
            self,
            lemma: LemmatizationToken
    ) -> 'Word':
        if self.is_compatible(lemma):
            return (
                self
                if lemma.unique_lemma is None
                else attr.evolve(self, unique_lemma=lemma.unique_lemma)
            )
        else:
            raise LemmatizationError()

    def is_compatible(self, lemma: LemmatizationToken) -> bool:
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = (
            (self.lemmatizable and lemma.unique_lemma is not None) or
            lemma.unique_lemma in [tuple(), None]
        )
        return value_is_compatible and lemma_is_compatible

    def accept(self, visitor: Any) -> None:
        visitor.visit_word(self)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Word',
            'uniqueLemma': [*self.unique_lemma],
            'normalized': self.normalized,
            'language': self.language.name,
            'lemmatizable': self.lemmatizable
        }


@attr.s(auto_attribs=True, frozen=True)
class LoneDeterminative(Word):
    _partial: Partial = Partial(False, False)

    @staticmethod
    def of_value(value: str, partial: Partial) -> 'LoneDeterminative':
        return LoneDeterminative(value, partial=partial)

    @property
    def lemmatizable(self) -> bool:
        return False

    @property
    def partial(self) -> Partial:
        return self._partial

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LoneDeterminative',
            'partial': list(self.partial)
        }


@attr.s(frozen=True)
class LanguageShift(Token):
    _normalization_shift = '%n'

    @property
    def language(self):
        return Language.of_atf(self.value)

    @property
    def normalized(self):
        return self.value == LanguageShift._normalization_shift

    def accept(self, visitor: Any) -> None:
        visitor.visit_language_shift(self)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LanguageShift',
            'normalized': self.normalized,
            'language': self.language.name
        }


@attr.s(frozen=True)
class DocumentOrientedGloss(Token):
    def accept(self, visitor: Any) -> None:
        visitor.visit_document_oriented_gloss(self)

    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '{(' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'DocumentOrientedGloss'
        }


@attr.s(auto_attribs=True, frozen=True)
class Erasure(Token):
    side: Side

    def accept(self, visitor: Any) -> None:
        visitor.visit_erasure(self)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Erasure',
            'side': self.side.name
        }


@attr.s(frozen=True)
class LineContinuation(Token):
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LineContinuation'
        }
