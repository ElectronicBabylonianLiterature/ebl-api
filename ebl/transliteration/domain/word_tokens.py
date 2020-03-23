import collections
from enum import Enum, auto
from typing import Optional, Sequence, Type, TypeVar

import attr

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.converters import convert_token_sequence
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_cleaner import clean_word

DEFAULT_LANGUAGE = Language.AKKADIAN
DEFAULT_NORMALIZED = False
Partial = collections.namedtuple("Partial", "start end")


class ErasureState(Enum):
    NONE = auto()
    ERASED = auto()
    OVER_ERASED = auto()


T = TypeVar("T", bound="Word")


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Sequence[WordId] = tuple()
    erasure: ErasureState = ErasureState.NONE
    alignment: Optional[int] = None
    _parts: Sequence[Token] = attr.ib(default=tuple(), converter=convert_token_sequence)

    @classmethod
    def of(
        cls: Type[T],
        parts: Sequence[Token],
        language: Language = DEFAULT_LANGUAGE,
        normalized: bool = DEFAULT_NORMALIZED,
        unique_lemma: Sequence[WordId] = tuple(),
        erasure: ErasureState = ErasureState.NONE,
        alignment: Optional[int] = None,
    ) -> T:
        return cls(
            frozenset(), language, normalized, unique_lemma, erasure, alignment, parts
        )

    @property
    def value(self) -> str:
        return "".join(part.value for part in self.parts)

    @property
    def lemmatizable(self) -> bool:
        non_lemmatizables = [
            atf.VARIANT_SEPARATOR,
            atf.UNCLEAR_SIGN,
            atf.UNIDENTIFIED_SIGN,
            atf.UNKNOWN_NUMBER_OF_SIGNS,
        ]
        return (
            self.language.lemmatizable
            and not self.normalized
            and self.erasure is not ErasureState.ERASED
            and all((substring not in self.value) for substring in non_lemmatizables)
            and not any(self.partial)
        )

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    @property
    def partial(self) -> Partial:
        partials = [
            *[joiner.value for joiner in atf.Joiner],
            atf.UNKNOWN_NUMBER_OF_SIGNS,
        ]
        return Partial(
            any(self.value.startswith(partial) for partial in partials),
            any(self.value.endswith(partial) for partial in partials),
        )

    def set_language(self, language: Language, normalized: bool) -> "Word":
        return attr.evolve(self, language=language, normalized=normalized)

    def set_erasure(self, erasure: ErasureState,) -> "Word":
        return attr.evolve(self, erasure=erasure)

    def set_unique_lemma(self, lemma: LemmatizationToken) -> "Word":
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = self.lemmatizable or not lemma.unique_lemma
        if value_is_compatible and lemma_is_compatible:
            return attr.evolve(self, unique_lemma=lemma.unique_lemma or tuple())
        else:
            raise LemmatizationError(f"Cannot apply {lemma} to {self}.")

    def set_alignment(self, alignment: AlignmentToken):
        if self.value == alignment.value and (
            self.alignable or alignment.alignment is None
        ):
            return attr.evolve(self, alignment=alignment.alignment)
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
            result = result.set_alignment(AlignmentToken(token.value, self.alignment))
        return result


@attr.s(auto_attribs=True, frozen=True)
class LoneDeterminative(Word):
    @staticmethod
    def of_value(
        parts, erasure: ErasureState = ErasureState.NONE
    ) -> "LoneDeterminative":
        return LoneDeterminative.of(parts, erasure=erasure)

    @property
    def lemmatizable(self) -> bool:
        return False


@attr.s(auto_attribs=True, frozen=True)
class InWordNewline(Token):
    @property
    def value(self) -> str:
        return atf.IN_WORD_NEWLINE

    @property
    def parts(self):
        return tuple()
