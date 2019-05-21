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


class ValidationState:
    def __init__(self):
        self._enclosures = {
            EnclosureType.BROKEN_OFF: False,
            EnclosureType.MAYBE_BROKEN_OFF: False
        }

    @property
    def open_enclosures(self):
        return [type_
                for type_, open_ in self._enclosures.items()
                if open_]

    def open(self, type_: EnclosureType) -> None:
        self._enclosures[type_] = True

    def close(self, type_: EnclosureType) -> None:
        self._enclosures[type_] = False

    def can_open(self, type_: EnclosureType) -> bool:
        is_closed = not self._enclosures[type_]
        parent_is_open = self._enclosures.get(type_.parent, True)
        return is_closed and parent_is_open

    def can_close(self, type_: EnclosureType) -> bool:
        is_open = self._enclosures[type_]
        children_are_not_open = not [
            child_type
            for child_type, open_
            in self._enclosures.items()
            if open_ and child_type.parent is type_
        ]
        return is_open and children_are_not_open


class EnclosureValidator(EnclosureVisitor):
    def __init__(self):
        self._state = ValidationState()

    def visit_enclosure(self, enclosure: Enclosure) -> None:
        if enclosure.is_open and self._state.can_open(enclosure.type):
            self._state.open(enclosure.type)
        elif enclosure.is_close and self._state.can_close(enclosure.type):
            self._state.close(enclosure.type)
        else:
            raise EnclosureError(f'Unexpected enclosure {enclosure}.')

    def validate_end_state(self):
        open_enclosures = self._state.open_enclosures
        if open_enclosures:
            raise EnclosureError(f'Unclosed enclosure {open_enclosures}.')
