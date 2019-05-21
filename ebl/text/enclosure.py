from abc import ABC
from enum import unique, Enum


@unique
class EnclosureType(Enum):
    BROKEN_OFF = '[]'
    MAYBE_BROKEN_OFF = '()'


@unique
class EnclosureVariant(Enum):
    OPEN = 0
    CLOSE = 1


@unique
class Enclosure(Enum):
    BROKEN_OFF_OPEN = (EnclosureType.BROKEN_OFF, EnclosureVariant.OPEN)
    BROKEN_OFF_CLOSE = (EnclosureType.BROKEN_OFF, EnclosureVariant.CLOSE)
    MAYBE_BROKEN_OFF_OPEN = (EnclosureType.MAYBE_BROKEN_OFF,
                             EnclosureVariant.OPEN)
    MAYBE_BROKEN_OFF_CLOSE = (EnclosureType.MAYBE_BROKEN_OFF,
                              EnclosureVariant.CLOSE)

    def __init__(self, type_: EnclosureType, variant: EnclosureVariant):
        self.type = type_
        self.variant = variant

    def accept(self, visitor: 'EnclosureVisitor') -> None:
        visitor.visit_enclosure(self)

    def __str__(self) -> str:
        return self.type.value[self.variant.value]


class EnclosureVisitor(ABC):

    def visit_enclosure(self, enclosure: Enclosure) -> None:
        ...
