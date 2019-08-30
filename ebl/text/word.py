import collections
from enum import Enum, auto
from typing import Optional, Tuple

import attr
import pydash

from ebl.corpus.alignment import AlignmentError, AlignmentToken
from ebl.dictionary.word import WordId
from ebl.text.atf import JOINERS, UNCLEAR_SIGN, UNIDENTIFIED_SIGN, \
    VARIANT_SEPARATOR
from ebl.text.language import Language
from ebl.text.lemmatization import LemmatizationError, LemmatizationToken
from ebl.text.token import Token
from ebl.text.token_visitor import TokenVisitor
from ebl.text.word_cleaner import clean_word

DEFAULT_LANGUAGE = Language.AKKADIAN
DEFAULT_NORMALIZED = False
Partial = collections.namedtuple('Partial', 'start end')


class ErasureState(Enum):
    NONE = auto()
    ERASED = auto()
    OVER_ERASED = auto()


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Tuple[WordId, ...] = tuple()
    erasure: ErasureState = ErasureState.NONE
    alignment: Optional[int] = None

    @property
    def lemmatizable(self) -> bool:
        non_lemmatizable_chars = {
            VARIANT_SEPARATOR,
            UNCLEAR_SIGN,
            UNIDENTIFIED_SIGN
        }
        return (
                self.language.lemmatizable and
                not self.normalized and
                self.erasure is not ErasureState.ERASED and
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
                in JOINERS
            ),
            any(
                self.value.endswith(joiner)
                for joiner
                in JOINERS
            )
        )

    def set_language(self, language: Language, normalized: bool) -> 'Word':
        return attr.evolve(self, language=language, normalized=normalized)

    def set_erasure(self, erasure: ErasureState, ) -> 'Word':
        return attr.evolve(self, erasure=erasure)

    def set_unique_lemma(
            self,
            lemma: LemmatizationToken
    ) -> 'Word':
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = (
            (self.lemmatizable and lemma.unique_lemma is not None) or
            lemma.unique_lemma in [tuple(), None]
        )
        if value_is_compatible and lemma_is_compatible:
            return (
                self
                if lemma.unique_lemma is None
                else attr.evolve(self, unique_lemma=lemma.unique_lemma)
            )
        else:
            raise LemmatizationError(f'Cannot apply {lemma} to {self}.')

    def set_alignment(self, alignment: AlignmentToken):
        if (
                self.value == alignment.value
                and (self.alignable or alignment.alignment is None)
        ):
            return attr.evolve(
                self,
                alignment=alignment.alignment
            )
        else:
            raise AlignmentError()

    def strip_alignment(self):
        return attr.evolve(self, alignment=None)

    def merge(self, token: Token) -> Token:
        clean_values_are_equal =\
            clean_word(self.value) == clean_word(token.value)

        if type(token) == Word and clean_values_are_equal:
            result = token
            if token.lemmatizable:
                result = result.set_unique_lemma(
                    LemmatizationToken(token.value, self.unique_lemma)
                )
            if token.alignable:
                result = result.set_alignment(
                    AlignmentToken(token.value, self.alignment)
                )
            return result
        else:
            return token

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_word(self)

    def to_dict(self) -> dict:
        return pydash.omit_by({
            **super().to_dict(),
            'type': 'Word',
            'uniqueLemma': [*self.unique_lemma],
            'normalized': self.normalized,
            'language': self.language.name,
            'lemmatizable': self.lemmatizable,
            'erasure': self.erasure.name,
            'alignment': self.alignment
        }, lambda value: value is None)


@attr.s(auto_attribs=True, frozen=True)
class LoneDeterminative(Word):
    _partial: Partial = Partial(False, False)

    @staticmethod
    def of_value(value: str,
                 partial: Partial,
                 erasure: ErasureState = ErasureState.NONE) -> \
            'LoneDeterminative':
        return LoneDeterminative(value, erasure=erasure, partial=partial)

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
