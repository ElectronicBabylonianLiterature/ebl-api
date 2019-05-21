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


class EnclosureVisitor(ABC):
    @abstractmethod
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
        if self._can_open(enclosure):
            self._state[enclosure.type] = True
        elif self._can_close(enclosure):
            self._state[enclosure.type] = False
        else:
            raise EnclosureError(f'Unexpected enclosure {enclosure}.')

    def _can_open(self, enclosure: Enclosure) -> bool:
        is_closed = not self._state[enclosure.type]
        parent_is_open = self._state.get(enclosure.type.parent, True)
        return enclosure.is_open and is_closed and parent_is_open

    def _can_close(self, enclosure: Enclosure) -> bool:
        is_open = self._state[enclosure.type]
        children_are_not_open = not [
            type_
            for type_, open_
            in self._state.items()
            if open_ and type_.parent is enclosure.type
        ]
        return enclosure.is_close and is_open and children_are_not_open

    def validate_end_state(self):
        open_enclosures = [type_
                           for type_, open_ in self._state.items()
                           if open_]
        if open_enclosures:
            raise EnclosureError(f'Unclosed enclosure {open_enclosures}.')
