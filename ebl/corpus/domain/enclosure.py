from enum import Enum, unique

import attr


@unique
class EnclosureVariant(Enum):
    OPEN = 0
    CLOSE = 1


@unique
class EnclosureType(Enum):
    BROKEN_OFF = ("[", "]", None)
    MAYBE_BROKEN_OFF = ("(", ")", BROKEN_OFF)
    EMENDATION = ("<", ">", None)

    def __init__(self, open_: str, close: str, parent: "EnclosureType"):
        self._delimiters = {EnclosureVariant.OPEN: open_, EnclosureVariant.CLOSE: close}
        self.parent = parent

    def get_delimiter(self, variant: EnclosureVariant) -> str:
        return self._delimiters[variant]

    def __str__(self) -> str:
        return "".join(self._delimiters.values())


@attr.s(auto_attribs=True, frozen=True)
class Enclosure:
    type: EnclosureType
    _variant: EnclosureVariant

    @property
    def is_open(self) -> bool:
        return self._variant is EnclosureVariant.OPEN

    @property
    def is_close(self) -> bool:
        return self._variant is EnclosureVariant.CLOSE

    def accept(self, visitor: "EnclosureVisitor") -> None:
        visitor.visit_enclosure(self)

    def __str__(self) -> str:
        return self.type.get_delimiter(self._variant)


class EnclosureVisitor:
    def visit_enclosure(self, enclosure: Enclosure) -> None:
        pass


BROKEN_OFF_OPEN = Enclosure(EnclosureType.BROKEN_OFF, EnclosureVariant.OPEN)
BROKEN_OFF_CLOSE = Enclosure(EnclosureType.BROKEN_OFF, EnclosureVariant.CLOSE)
MAYBE_BROKEN_OFF_OPEN = Enclosure(EnclosureType.MAYBE_BROKEN_OFF, EnclosureVariant.OPEN)
MAYBE_BROKEN_OFF_CLOSE = Enclosure(
    EnclosureType.MAYBE_BROKEN_OFF, EnclosureVariant.CLOSE
)
EMENDATION_OPEN = Enclosure(EnclosureType.EMENDATION, EnclosureVariant.OPEN)
EMENDATION_CLOSE = Enclosure(EnclosureType.EMENDATION, EnclosureVariant.CLOSE)
