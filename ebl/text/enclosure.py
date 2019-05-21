from abc import ABC, abstractmethod
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

    @property
    def is_open(self) -> bool:
        return self.variant is EnclosureVariant.OPEN

    @property
    def is_close(self) -> bool:
        return self.variant is EnclosureVariant.CLOSE

    def accept(self, visitor: 'EnclosureVisitor') -> None:
        visitor.visit_enclosure(self)

    def __str__(self) -> str:
        return self.type.value[self.variant.value]


class EnclosureVisitor(ABC):
    @abstractmethod
    def visit_enclosure(self, enclosure: Enclosure) -> None:
        ...


class EnclosureError(Exception):
    pass


class EnclosureValidator(EnclosureVisitor):
    expected = {
        EnclosureType.BROKEN_OFF: None,
        EnclosureType.MAYBE_BROKEN_OFF: EnclosureType.BROKEN_OFF
    }

    def __init__(self):
        self._state = {
            EnclosureType.BROKEN_OFF: False,
            EnclosureType.MAYBE_BROKEN_OFF: False
        }

    def visit_enclosure(self, enclosure: Enclosure) -> None:
        if self._can_open(enclosure):
            self._state[enclosure.type] = True
        elif self._can_close(enclosure):
            self._state[enclosure.type] = False
        else:
            raise EnclosureError(f'Unexpected enclosure {enclosure}.')

    def _can_open(self, enclosure: Enclosure) -> bool:
        expected_type = self.expected[enclosure.type]
        return (enclosure.is_open and
                not self._state[enclosure.type] and
                (not expected_type or self._state[expected_type]))

    def _can_close(self, enclosure: Enclosure) -> bool:
        return (enclosure.is_close and
                self._state[enclosure.type] and
                not [type_
                     for type_, open_
                     in self._state.items()
                     if open_ and self.expected[type_] is enclosure.type])

    def validate_end_state(self):
        open_enclosures = [type_
                           for type_, open_ in self._state.items()
                           if open_]
        if open_enclosures:
            raise EnclosureError(f'Unclosed enclosure {open_enclosures}.')
