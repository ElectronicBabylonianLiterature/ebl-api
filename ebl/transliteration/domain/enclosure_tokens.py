from enum import Enum, auto

import attr

from ebl.transliteration.domain.tokens import ValueToken


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
class Erasure(ValueToken):
    side: Side


@attr.s(frozen=True)
class OmissionOrRemoval(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if (self.value in ["<(", "<", "<<"]) else Side.RIGHT
