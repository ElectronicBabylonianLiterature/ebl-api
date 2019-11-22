import collections
from enum import Enum, auto
from typing import Iterable, Tuple, Optional, Sequence

import attr
import pydash

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.alignment import AlignmentToken, AlignmentError
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import LemmatizationToken, \
    LemmatizationError
from ebl.transliteration.domain.tokens import ValueToken, Token
from ebl.transliteration.domain.word_cleaner import clean_word

DEFAULT_LANGUAGE = Language.AKKADIAN
DEFAULT_NORMALIZED = False
Partial = collections.namedtuple('Partial', 'start end')


def convert_token_sequence(tokens: Iterable['Token']) -> Tuple['Token', ...]:
    return tuple(tokens)


class ErasureState(Enum):
    NONE = auto()
    ERASED = auto()
    OVER_ERASED = auto()


@attr.s(auto_attribs=True, frozen=True)
class Word(ValueToken):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Tuple[WordId, ...] = tuple()
    erasure: ErasureState = ErasureState.NONE
    alignment: Optional[int] = None
    _parts: Sequence[Token] = attr.ib(default=tuple(),
                                      kw_only=True,
                                      converter=convert_token_sequence)

    @property
    def lemmatizable(self) -> bool:
        non_lemmatizables = [
            atf.VARIANT_SEPARATOR,
            atf.UNCLEAR_SIGN,
            atf.UNIDENTIFIED_SIGN,
            atf.UNKNOWN_NUMBER_OF_SIGNS
        ]
        return (
                self.language.lemmatizable and
                not self.normalized and
                self.erasure is not ErasureState.ERASED and
                all((substring not in self.value)
                    for substring
                    in non_lemmatizables) and
                not any(self.partial)
        )

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    @property
    def partial(self) -> Partial:
        partials = [
            *[joiner.value for joiner in atf.Joiner],
            atf.UNKNOWN_NUMBER_OF_SIGNS
        ]
        return Partial(
            any(
                self.value.startswith(partial)
                for partial
                in partials
            ),
            any(
                self.value.endswith(partial)
                for partial
                in partials
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
        lemma_is_compatible = self.lemmatizable or not lemma.unique_lemma
        if value_is_compatible and lemma_is_compatible:
            return attr.evolve(self,
                               unique_lemma=lemma.unique_lemma or tuple())
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
        same_value = clean_word(self.value) == clean_word(token.value)
        is_compatible = type(token) == Word and same_value

        result = token
        if is_compatible and token.lemmatizable:
            result = result.set_unique_lemma(
                LemmatizationToken(token.value, self.unique_lemma)
            )
        if is_compatible and token.alignable:
            result = result.set_alignment(
                AlignmentToken(token.value, self.alignment)
            )
        return result

    def to_dict(self) -> dict:
        return pydash.omit_by({
            **super().to_dict(),
            'type': 'Word',
            'uniqueLemma': [*self.unique_lemma],
            'normalized': self.normalized,
            'language': self.language.name,
            'lemmatizable': self.lemmatizable,
            'erasure': self.erasure.name,
            'alignment': self.alignment,
            'parts': [token.to_dict() for token in self.parts]
        }, lambda value: value is None)


@attr.s(auto_attribs=True, frozen=True)
class LoneDeterminative(Word):
    _partial: Partial = attr.ib(default=Partial(False, False), kw_only=True)

    @staticmethod
    def of_value(value: str,
                 partial: Partial,
                 erasure: ErasureState = ErasureState.NONE,
                 parts=tuple()) -> 'LoneDeterminative':
        return LoneDeterminative(value,
                                 erasure=erasure,
                                 partial=partial,
                                 parts=parts)

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


@attr.s(auto_attribs=True, frozen=True)
class Joiner(Token):
    _value: atf.Joiner

    @property
    def value(self):
        return self._value.value

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Joiner'
        }
