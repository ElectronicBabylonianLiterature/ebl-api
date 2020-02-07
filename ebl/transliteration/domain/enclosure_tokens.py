from abc import abstractmethod
from typing import Sequence, Mapping

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.tokens import ValueToken, Token, convert_token_sequence


@attr.s(frozen=True)
class OmissionOrRemoval(ValueToken):
    """This class is deprecated and kept only for backwards compatibility.
    Omission, AccidentalOmission, or Removal should be used instead."""

    @property
    def side(self) -> Side:
        return Side.LEFT if (self.value in ["<(", "<", "<<"]) else Side.RIGHT


@attr.s(auto_attribs=True, frozen=True)
class Enclosure(Token):
    side: Side

    @staticmethod
    @abstractmethod
    def get_sides() -> Mapping[Side, str]:
        ...

    @property
    def value(self):
        return self.get_sides()[self.side]

    @classmethod
    def open(cls):
        return cls(Side.LEFT)

    @classmethod
    def close(cls):
        return cls(Side.RIGHT)

    @classmethod
    def of_value(cls, value: str):
        sides = cls.get_sides()
        side = {v: k for k, v in sides.items()}[value]
        return cls(side)


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
    def center(cls):
        return cls(Side.CENTER)


@attr.s(auto_attribs=True, frozen=True)
class Gloss(Token):
    _parts: Sequence[Token] = attr.ib(converter=convert_token_sequence)

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
