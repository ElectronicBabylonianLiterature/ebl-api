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


class EnclosureError(Exception):
    pass


class EnclosureValidator(EnclosureVisitor):
    def __init__(self):
        self._state = {
            EnclosureType.BROKEN_OFF: False,
            EnclosureType.MAYBE_BROKEN_OFF: False
        }

    def visit_enclosure(self, enclosure: Enclosure) -> None:
        expected = {
            EnclosureType.BROKEN_OFF: None,
            EnclosureType.MAYBE_BROKEN_OFF: EnclosureType.BROKEN_OFF
        }
        expected_type = expected[enclosure.type]
        if (enclosure.variant is EnclosureVariant.OPEN and
                not self._state[enclosure.type] and
                (not expected_type or self._state[expected_type])):
            self._state[enclosure.type] = True
        elif (enclosure.variant is EnclosureVariant.CLOSE and
              self._state[enclosure.type] and
              not [type_
                   for type_, open_
                   in self._state.items()
                   if open_ and expected[type_] is enclosure.type]):
            self._state[enclosure.type] = False
        else:
            raise EnclosureError(f'Unexpected enclosure {enclosure}.')

    def validate_end_state(self):
        open_enclosures = [type_
                           for type_, open_ in self._state.items()
                           if open_]
        if open_enclosures:
            raise EnclosureError(f'Unclosed enclosure {open_enclosures}.')
