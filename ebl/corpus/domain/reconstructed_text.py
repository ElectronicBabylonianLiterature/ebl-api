from abc import abstractmethod
from enum import Enum, unique
from typing import Sequence, Type, TypeVar

import attr
import pydash  # pyre-ignore[21]

from ebl.transliteration.domain.enclosure_tokens import Enclosure
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    TokenVisitor,
    UnknownNumberOfSigns,
)


@attr.s(frozen=True, str=False)
class ReconstructionToken(Token):
    @property
    def value(self) -> str:
        return str(self)


@unique
class Modifier(Enum):
    DAMAGED = "#"
    UNCERTAIN = "?"
    CORRECTED = "!"


@attr.s(auto_attribs=True, frozen=True, str=False)
class AkkadianWord(ReconstructionToken):

    _parts: Sequence[Token]
    modifiers: Sequence[Modifier] = tuple()

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_akkadian_word(self)

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    def __str__(self) -> str:
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
        parts: Sequence[Token], modifier: Sequence[Modifier] = tuple()
    ) -> "AkkadianWord":
        return AkkadianWord(frozenset(), ErasureState.NONE, parts, modifier)


@attr.s(auto_attribs=True, frozen=True, str=False)
class Lacuna(ReconstructionToken):
    _before: Sequence[Enclosure]
    _after: Sequence[Enclosure]

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_lacuna(self)

    @property
    def parts(self) -> Sequence[Token]:
        return [*self._before, UnknownNumberOfSigns.of(), *self._after]

    def __str__(self):
        return "".join(part.value for part in self.parts)

    @staticmethod
    def of(before: Sequence[Enclosure], after: Sequence[Enclosure]) -> "Lacuna":
        return Lacuna(frozenset(), ErasureState.NONE, before, after)


T = TypeVar("T", bound="Break")


@attr.s(auto_attribs=True, frozen=True, str=False)
class Break(ReconstructionToken):
    is_uncertain: bool

    @property
    @abstractmethod
    def _value(self) -> str:
        ...

    @property
    def parts(self) -> Sequence["Token"]:
        return tuple()

    def __str__(self) -> str:
        return f"({self._value})" if self.is_uncertain else self._value

    @classmethod
    def certain(cls: Type[T]) -> T:
        return cls(frozenset(), ErasureState.NONE, False)

    @classmethod
    def uncertain(cls: Type[T]) -> T:
        return cls(frozenset(), ErasureState.NONE, True)


@attr.s(frozen=True, str=False)
class Caesura(Break):
    @property
    def _value(self) -> str:
        return "||"

    def accept(self, visitor: TokenVisitor):
        visitor.visit_caesura(self)


@attr.s(frozen=True, str=False)
class MetricalFootSeparator(Break):
    @property
    def _value(self) -> str:
        return "|"

    def accept(self, visitor: TokenVisitor):
        visitor.visit_metrical_foot_separator(self)
