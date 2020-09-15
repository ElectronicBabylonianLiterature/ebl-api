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
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor

DEFAULT_LANGUAGE: Language = Language.AKKADIAN
DEFAULT_NORMALIZED = False


T = TypeVar("T", bound="Word")


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Sequence[WordId] = tuple()
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
            frozenset(), erasure, language, normalized, unique_lemma, alignment, parts
        )

    @property
    def value(self) -> str:
        return "".join(part.value for part in self.parts)

    @property
    def clean_value(self) -> str:
        return "".join(
            part.clean_value
            for part in self.parts
            if part.erasure != ErasureState.ERASED
        )

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
        )

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    def set_language(self, language: Language, normalized: bool) -> "Word":
        return attr.evolve(self, language=language, normalized=normalized)

    def set_unique_lemma(self, lemma: LemmatizationToken) -> "Word":
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = self.lemmatizable or not lemma.unique_lemma
        if value_is_compatible and lemma_is_compatible:
            return attr.evolve(self, unique_lemma=lemma.unique_lemma or tuple())
        else:
            raise LemmatizationError(f"Cannot apply {lemma} to {self}.")

    def set_alignment(self, alignment: AlignmentToken) -> "Word":
        if self.value == alignment.value and (
            self.alignable or alignment.alignment is None
        ):
            return attr.evolve(self, alignment=alignment.alignment)
        else:
            raise AlignmentError()

    def strip_alignment(self) -> "Word":
        return attr.evolve(self, alignment=None)

    def merge(self, token: Token) -> Token:
        same_value = self.clean_value == token.clean_value
        is_compatible = type(token) == Word and same_value

        result = token
        if is_compatible and token.lemmatizable:
            result = result.set_unique_lemma(
                LemmatizationToken(token.value, self.unique_lemma)
            )
        if is_compatible and token.alignable:
            result = result.set_alignment(AlignmentToken(token.value, self.alignment))
        return result

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_word(self)


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

    @staticmethod
    def of() -> "InWordNewline":
        return InWordNewline(frozenset(), ErasureState.NONE)
