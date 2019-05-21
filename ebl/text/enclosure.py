from abc import ABC, abstractmethod
from enum import Enum, unique


@unique
class EnclosureVariant(Enum):
    OPEN = 0
    CLOSE = 1


@unique
class EnclosureType(Enum):
    BROKEN_OFF = ('[', ']', None)
    MAYBE_BROKEN_OFF = ('(', ')', BROKEN_OFF)

    def __init__(self, open_: str, close: str, parent: 'EnclosureType'):
        self._delimiters = {
            EnclosureVariant.OPEN: open_,
            EnclosureVariant.CLOSE: close
        }
        self.parent = parent

    def get_delimiter(self, variant: EnclosureVariant) -> str:
        return self._delimiters[variant]

    def __str__(self) -> str:
        return ''.join(self._delimiters.values())


class Enclosure:
    def __init__(self, type_: EnclosureType, variant: EnclosureVariant):
        self.type = type_
        self._variant = variant

    @property
    def is_open(self) -> bool:
        return self._variant is EnclosureVariant.OPEN

    @property
    def is_close(self) -> bool:
        return self._variant is EnclosureVariant.CLOSE

    def accept(self, visitor: 'EnclosureVisitor') -> None:
        visitor.visit_enclosure(self)

    def __str__(self) -> str:
        return self.type.get_delimiter(self._variant)


Enclosures = Enum('Enclosure', [
    (f'{type_.name}_OPEN', (type_, EnclosureVariant.OPEN))
    for type_ in EnclosureType
] + [
    (f'{type_.name}_CLOSE', (type_, EnclosureVariant.CLOSE))
    for type_ in EnclosureType
], type=Enclosure)  # type: ignore


class EnclosureVisitor(ABC):
    @abstractmethod
    def visit_enclosure(self, enclosure: Enclosure) -> None:
        ...
