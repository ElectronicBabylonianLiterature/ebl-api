from abc import abstractmethod
from typing import Optional, Sequence, Type, TypeVar

import attr

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.converters import convert_token_sequence
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor


A = TypeVar("A", bound="AbstractWord")
T = TypeVar("T", bound=Token)


@attr.s(auto_attribs=True, frozen=True)
class AbstractWord(Token):
    unique_lemma: Sequence[WordId] = tuple()
    alignment: Optional[int] = None
    _parts: Sequence[Token] = attr.ib(default=tuple(), converter=convert_token_sequence)
    variant: Optional["AbstractWord"] = None

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

    def set_alignment(
        self: A, alignment: Optional[int], variant: Optional["AbstractWord"]
    ) -> A:
        return attr.evolve(self, alignment=alignment, variant=variant)

    def strip_alignment(self: A) -> A:
        return attr.evolve(self, alignment=None, variant=None)

    def merge(self, token: T) -> T:
        if isinstance(token, AbstractWord):
            return self._merge_word(token)
        else:
            return token

    def _merge_word(self, token: A) -> A:
        is_compatible = self._is_compatible(token)
        result = token

        if is_compatible and token.lemmatizable:
            result = result.set_unique_lemma(
                LemmatizationToken(token.value, self.unique_lemma)
            )
        if is_compatible and token.alignable:
            result = result.set_alignment(self.alignment, self.variant)

        return result

    def _is_compatible(self, token: Token) -> bool:
        same_value = self.clean_value == token.clean_value
        same_type = type(token) == type(self)
        return same_type and same_value


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
        variant: Optional[AbstractWord] = None,
    ) -> W:
        return cls(
            frozenset(),
            erasure,
            unique_lemma,
            alignment,
            parts,
            variant,
            language,
            normalized,
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
