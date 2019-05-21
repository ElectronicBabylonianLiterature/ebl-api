from ebl.text.enclosure import EnclosureType, EnclosureVisitor, Enclosure


class EnclosureError(Exception):
    pass


class ValidationState:
    def __init__(self):
        self._enclosures = {type_: False for type_ in EnclosureType}

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
