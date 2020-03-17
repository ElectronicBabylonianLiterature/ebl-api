from abc import abstractmethod
from typing import Mapping, Sequence, TypeVar, Type

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.tokens import Token, ValueToken, convert_token_sequence


@attr.s(frozen=True)
class OmissionOrRemoval(ValueToken):
    """This class is deprecated and kept only for backwards compatibility.
    Omission, AccidentalOmission, or Removal should be used instead."""

    @property
    def side(self) -> Side:
        return Side.LEFT if (self.value in ["<(", "<", "<<"]) else Side.RIGHT


E = TypeVar("E", bound="Enclosure")


@attr.s(auto_attribs=True, frozen=True)
class Enclosure(Token):
    side: Side

    @staticmethod
    @abstractmethod
    def get_sides() -> Mapping[Side, str]:
        ...

    @property
    def value(self) -> str:
        return self.get_sides()[self.side]

    @property
    def parts(self):
        return tuple()

    @property
    def is_open(self) -> bool:
        return self.side == Side.LEFT

    @property
    def is_close(self) -> bool:
        return self.side == Side.RIGHT

    @classmethod
    def open(cls: Type[E]) -> E:
        return cls(frozenset(), Side.LEFT)

    @classmethod
    def close(cls: Type[E]) -> E:
        return cls(frozenset(), Side.RIGHT)

    @classmethod
    def of(cls: Type[E], side: Side) -> E:
        return cls(frozenset(), side)

    @classmethod
    def of_value(cls: Type[E], value: str) -> E:
        sides = cls.get_sides()
        side = {v: k for k, v in sides.items()}[value]
        return cls(frozenset(), side)


@attr.s(frozen=True)
class DocumentOrientedGloss(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.DOCUMENT_ORIENTED_GLOSS


@attr.s(frozen=True)
class BrokenAway(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.BROKEN_AWAY


@attr.s(frozen=True)
class PerhapsBrokenAway(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.PERHAPS_BROKEN_AWAY


@attr.s(frozen=True)
class AccidentalOmission(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.ACCIDENTAL_OMISSION


@attr.s(frozen=True)
class IntentionalOmission(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.INTENTIONAL_OMISSION


@attr.s(frozen=True)
class Removal(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.REMOVAL


@attr.s(frozen=True)
class Erasure(Enclosure):
    @staticmethod
    def get_sides() -> Mapping[Side, str]:
        return atf.ERASURE

    @classmethod
    def center(cls) -> "Erasure":
        return cls(frozenset(), Side.CENTER)


G = TypeVar("G", bound="Gloss")


@attr.s(auto_attribs=True, frozen=True)
class Gloss(Token):
    _parts: Sequence[Token] = attr.ib(converter=convert_token_sequence)

    @classmethod
    def of(cls: Type[G], parts: Sequence[Token] = tuple()) -> G:
        return cls(frozenset(), parts)

    @property
    @abstractmethod
    def open(self) -> str:
        ...

    @property
    @abstractmethod
    def close(self) -> str:
        ...

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    @property
    def value(self) -> str:
        parts = "".join(token.value for token in self.parts)
        return f"{self.open}{parts}{self.close}"


@attr.s(auto_attribs=True, frozen=True)
class Determinative(Gloss):
    @property
    def open(self) -> str:
        return "{"

    @property
    def close(self) -> str:
        return "}"


@attr.s(auto_attribs=True, frozen=True)
class PhoneticGloss(Gloss):
    @property
    def open(self) -> str:
        return "{+"

    @property
    def close(self) -> str:
        return "}"


@attr.s(auto_attribs=True, frozen=True)
class LinguisticGloss(Gloss):
    @property
    def open(self) -> str:
        return "{{"

    @property
    def close(self) -> str:
        return "}}"
