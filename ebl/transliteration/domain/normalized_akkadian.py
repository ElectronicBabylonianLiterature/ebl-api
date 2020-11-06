from abc import abstractmethod
from typing import Optional, Sequence, Type, TypeVar

import attr
import pydash  # pyre-ignore[21]

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import Enclosure
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)


@attr.s(auto_attribs=True, frozen=True, str=False)
class AkkadianWord(Token):
    _parts: Sequence[Token]
    modifiers: Sequence[Flag] = attr.ib(default=tuple())
    unique_lemma: Sequence[WordId] = tuple()
    alignment: Optional[int] = None

    @modifiers.validator
    def _validate_modifiers(self, _, value):
        allowed_modifiers = set(Flag) - {Flag.COLLATION}
        if not set(value).issubset(allowed_modifiers):
            raise ValueError(f"Invalid modifiers: {value}")

    @property
    def lemmatizable(self) -> bool:
        return True

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    @property
    def value(self) -> str:
        last_parts = pydash.take_right_while(
            self.parts, lambda part: isinstance(part, Enclosure)
        )
        main_parts = self.parts[: len(self.parts) - len(last_parts)]
        return "".join(
            [part.value for part in main_parts]
            + [modifier.value for modifier in self.modifiers]
            + [part.value for part in last_parts]
        )

    @property
    def clean_value(self) -> str:
        return "".join(part.clean_value for part in self.parts)

    def set_unique_lemma(self, lemma: LemmatizationToken) -> "AkkadianWord":
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = self.lemmatizable or not lemma.unique_lemma
        if value_is_compatible and lemma_is_compatible:
            return attr.evolve(self, unique_lemma=lemma.unique_lemma or tuple())
        else:
            raise LemmatizationError(f"Cannot apply {lemma} to {self}.")

    def set_alignment(self, alignment: AlignmentToken) -> "AkkadianWord":
        if self.value == alignment.value and (
            self.alignable or alignment.alignment is None
        ):
            return attr.evolve(self, alignment=alignment.alignment)
        else:
            raise AlignmentError()

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_akkadian_word(self)

    @staticmethod
    def of(
        parts: Sequence[Token],
        modifier: Sequence[Flag] = tuple(),
        unique_lemma: Sequence[WordId] = tuple(),
        alignment: Optional[int] = None,
    ) -> "AkkadianWord":
        return AkkadianWord(
            frozenset(), ErasureState.NONE, parts, modifier, unique_lemma, alignment
        )


T = TypeVar("T", bound="Break")


@attr.s(auto_attribs=True, frozen=True, str=False)
class Break(Token):
    is_uncertain: bool

    @property
    @abstractmethod
    def _symbol(self) -> str:
        ...

    @property
    def parts(self) -> Sequence["Token"]:
        return tuple()

    @property
    def value(self) -> str:
        return f"({self._symbol})" if self.is_uncertain else self._symbol

    @classmethod
    def of(cls: Type[T], is_uncertain: bool) -> T:
        return cls(frozenset(), ErasureState.NONE, is_uncertain)

    @classmethod
    def certain(cls: Type[T]) -> T:
        return cls(frozenset(), ErasureState.NONE, False)

    @classmethod
    def uncertain(cls: Type[T]) -> T:
        return cls(frozenset(), ErasureState.NONE, True)


@attr.s(frozen=True, str=False)
class Caesura(Break):
    @property
    def _symbol(self) -> str:
        return "||"

    def accept(self, visitor: TokenVisitor):
        visitor.visit_caesura(self)


@attr.s(frozen=True, str=False)
class MetricalFootSeparator(Break):
    @property
    def _symbol(self) -> str:
        return "|"

    def accept(self, visitor: TokenVisitor):
        visitor.visit_metrical_foot_separator(self)
