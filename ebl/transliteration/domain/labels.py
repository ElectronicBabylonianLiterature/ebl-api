import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Iterable, Tuple

import attr
import roman
from parsy import char_from, regex, seq, string_from

from ebl.transliteration.domain.atf import Status, Surface


class LabelVisitor(ABC):
    @abstractmethod
    def visit_surface_label(self, label: "SurfaceLabel") -> "LabelVisitor":
        ...

    @abstractmethod
    def visit_column_label(self, label: "ColumnLabel") -> "LabelVisitor":
        ...

    @abstractmethod
    def visit_line_number_label(self, label: "LineNumberLabel") -> "LabelVisitor":
        ...


def no_duplicate_status(_instance, _attribute, value):
    if any(count > 1 for _, count in Counter(value).items()):
        raise ValueError(f'Duplicate status in "{value}".')


@attr.s(auto_attribs=True, frozen=True)
class Label(ABC):
    """ A label as defined in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    and
    http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html
    """

    status: Tuple[Status, ...] = attr.ib(validator=no_duplicate_status)

    @property
    @abstractmethod
    def _label(self) -> str:
        ...

    @property
    @abstractmethod
    def _atf(self) -> str:
        ...

    @property
    def _status_string(self) -> str:
        return "".join([status.value for status in self.status])

    @abstractmethod
    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        ...

    @staticmethod
    def parse(label: str) -> "Label":
        return LABEL.parse(label)

    def to_value(self) -> str:
        return f"{self._label}{self._status_string}"

    def to_atf(self) -> str:
        return f"{self._atf}{self._status_string}"


@attr.s(auto_attribs=True, frozen=True)
class ColumnLabel(Label):

    column: int

    @staticmethod
    def from_label(column: str, status: Iterable[Status] = tuple()) -> "ColumnLabel":
        return ColumnLabel(tuple(status), roman.fromRoman(column.upper()))

    @staticmethod
    def from_int(column: int, status: Iterable[Status] = tuple()) -> "ColumnLabel":
        return ColumnLabel(tuple(status), column)

    @property
    def _label(self) -> str:
        return roman.toRoman(self.column).lower()

    @property
    def _atf(self) -> str:
        return f"@column {self.column}"

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_column_label(self)


@attr.s(auto_attribs=True, frozen=True)
class SurfaceLabel(Label):

    surface: Surface

    @staticmethod
    def from_label(
        surface: Surface, status: Iterable[Status] = tuple()
    ) -> "SurfaceLabel":
        return SurfaceLabel(tuple(status), surface)

    @property
    def _label(self) -> str:
        return self.surface.label

    @property
    def _atf(self) -> str:
        return self.surface.atf

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_surface_label(self)


LINE_NUMBER_EXPRESSION = r"[^\s]+"


def is_sequence_of_non_space_characters(_instance, _attribute, value):
    if not re.fullmatch(LINE_NUMBER_EXPRESSION, value):
        raise ValueError(
            f'Line number "{value}" is not a sequence of ' "non-space characters."
        )


@attr.s(auto_attribs=True, frozen=True, init=False)
class LineNumberLabel(Label):

    number: str = attr.ib(validator=is_sequence_of_non_space_characters)

    def __init__(self, number: str):
        super().__init__(tuple())
        object.__setattr__(self, "number", number)
        attr.validate(self)

    @staticmethod
    def from_atf(atf: str) -> "LineNumberLabel":
        return LineNumberLabel(atf[:-1])

    @property
    def _label(self) -> str:
        return self.number

    @property
    def _atf(self) -> str:
        return f"{self.number}."

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_line_number_label(self)


STATUS = (
    char_from("".join([status.value for status in Status])).map(Status).desc("status")
)

SURFACE_LABEL = seq(
    string_from(*[surface.label for surface in Surface])
    .map(Surface.from_label)
    .desc("surface label"),
    STATUS.many(),
).combine(SurfaceLabel.from_label)
COLUMN_LABEL = seq(regex(r"[ivx]+").desc("column label"), STATUS.many()).combine(
    ColumnLabel.from_label
)
LINE_NUMBER_LABEL = (
    regex(LINE_NUMBER_EXPRESSION).map(LineNumberLabel).desc("line number label")
)
LABEL = SURFACE_LABEL | COLUMN_LABEL | LINE_NUMBER_LABEL
