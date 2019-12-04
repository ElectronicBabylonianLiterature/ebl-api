from enum import Enum, auto
from typing import Sequence

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.tokens import ValueToken, Token, convert_token_sequence


class Side(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


@attr.s(frozen=True)
class DocumentOrientedGloss(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == "{(" else Side.RIGHT


@attr.s(frozen=True)
class BrokenAway(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == "[" else Side.RIGHT


@attr.s(frozen=True)
class PerhapsBrokenAway(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == "(" else Side.RIGHT


@attr.s(auto_attribs=True, frozen=True)
class Erasure(Token):
    side: Side

    @property
    def value(self):
        return {
            Side.LEFT: atf.ERASURE_BOUNDARY,
            Side.CENTER: atf.ERASURE_DELIMITER,
            Side.RIGHT: atf.ERASURE_BOUNDARY,
        }[self.side]


@attr.s(frozen=True)
class OmissionOrRemoval(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if (self.value in ["<(", "<", "<<"]) else Side.RIGHT


@attr.s(auto_attribs=True, frozen=True)
class Determinative(Token):
    _parts: Sequence[Token] = attr.ib(converter=convert_token_sequence)

    @property
    def parts(self) -> Sequence["Token"]:
        return self._parts

    @property
    def value(self) -> str:
        parts = "".join(token.value for token in self.parts)
        return f"{{{parts}}}"


@attr.s(auto_attribs=True, frozen=True)
class PhoneticGloss(Token):
    _parts: Sequence[Token] = attr.ib(converter=convert_token_sequence)

    @property
    def parts(self) -> Sequence["Token"]:
        return self._parts

    @property
    def value(self) -> str:
        parts = "".join(token.value for token in self.parts)
        return f"{{+{parts}}}"
