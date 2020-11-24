from abc import abstractmethod
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


A = TypeVar("A", bound="AbstractWord")


@attr.s(auto_attribs=True, frozen=True)
class AbstractWord(Token):
    unique_lemma: Sequence[WordId] = tuple()
    alignment: Optional[int] = None
    _parts: Sequence[Token] = attr.ib(default=tuple(), converter=convert_token_sequence)

    @property
    @abstractmethod
    def language(self) -> Language:
        ...

    @property
    @abstractmethod
    def normalized(self) -> bool:
        ...

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

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
            and self.erasure is not ErasureState.ERASED
            and all((substring not in self.value) for substring in non_lemmatizables)
        )

    def set_unique_lemma(self: A, lemma: LemmatizationToken) -> A:
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = self.lemmatizable or not lemma.unique_lemma
        if value_is_compatible and lemma_is_compatible:
            return attr.evolve(self, unique_lemma=lemma.unique_lemma or tuple())
        else:
            raise LemmatizationError(f"Cannot apply {lemma} to {self}.")

    def set_alignment(self: A, alignment: AlignmentToken) -> A:
        if self.value == alignment.value and (
            self.alignable or alignment.alignment is None
        ):
            return attr.evolve(self, alignment=alignment.alignment)
        else:
            raise AlignmentError()

    def strip_alignment(self: A) -> A:
        return attr.evolve(self, alignment=None)

    def merge(self, token: Token) -> Token:
        same_value = self.clean_value == token.clean_value
        is_compatible = type(token) == type(self) and same_value

        result = token
        if is_compatible and token.lemmatizable:
            result = result.set_unique_lemma(
                LemmatizationToken(token.value, self.unique_lemma)
            )
        if is_compatible and token.alignable:
            result = result.set_alignment(AlignmentToken(token.value, self.alignment))
        return result


DEFAULT_LANGUAGE: Language = Language.AKKADIAN
DEFAULT_NORMALIZED = False
W = TypeVar("W", bound="Word")


@attr.s(auto_attribs=True, frozen=True)
class Word(AbstractWord):
    _language: Language = DEFAULT_LANGUAGE
    _normalized: bool = DEFAULT_NORMALIZED

    @classmethod
    def of(
        cls: Type[W],
        parts: Sequence[Token],
        language: Language = DEFAULT_LANGUAGE,
        normalized: bool = DEFAULT_NORMALIZED,
        unique_lemma: Sequence[WordId] = tuple(),
        erasure: ErasureState = ErasureState.NONE,
        alignment: Optional[int] = None,
    ) -> W:
        return cls(
            frozenset(), erasure, unique_lemma, alignment, parts, language, normalized
        )

    @property
    def language(self) -> Language:
        return self._language

    @property
    def normalized(self) -> bool:
        return self._normalized

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

    def set_language(self, language: Language, normalized: bool) -> "Word":
        return attr.evolve(self, language=language, normalized=normalized)

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
