from abc import abstractmethod
from typing import Sequence, Type, TypeVar

import attr
import pydash  # pyre-ignore[21]

from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import Enclosure
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor


@attr.s(auto_attribs=True, frozen=True, str=False)
class AkkadianWord(Token):
    _parts: Sequence[Token]
    modifiers: Sequence[Flag] = attr.ib(default=tuple())

    @modifiers.validator
    def _validate_modifiers(self, _, value):
        allowed_modifiers = set(Flag) - {Flag.COLLATION}
        if not set(value).issubset(allowed_modifiers):
            raise ValueError(f"Invalid modifiers: {value}")

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_akkadian_word(self)

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    @property
    def value(self) -> str:
        last_parts = pydash.take_right_while(
            list(self.parts), lambda part: isinstance(part, Enclosure)
        )
        main_parts = self.parts[: len(self.parts) - len(last_parts)]
        return "".join(
            [part.value for part in main_parts]
            + [modifier.value for modifier in self.modifiers]
            + [part.value for part in last_parts]
        )

    @staticmethod
    def of(
        parts: Sequence[Token], modifier: Sequence[Flag] = tuple()
    ) -> "AkkadianWord":
        return AkkadianWord(frozenset(), ErasureState.NONE, parts, modifier)


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
