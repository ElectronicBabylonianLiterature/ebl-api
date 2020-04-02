import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Iterable, Sequence, Tuple, Union

import attr
import roman  # pyre-ignore
from parsy import char_from, regex, seq, string_from  # pyre-ignore

from ebl.transliteration.domain.atf import Status, Surface


class DuplicateStatusError(ValueError):
    pass


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
    if any(count > 1 for count in Counter(value).values()):
        raise DuplicateStatusError(f'Duplicate status in "{value}".')


def convert_status_sequence(
    status: Union[Iterable[Status], Sequence[Status]]
) -> Tuple[Status, ...]:
    return tuple(status)


@attr.s(auto_attribs=True, frozen=True)
class Label(ABC):
    """ A label as defined in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    and
    http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html
    """

    status: Sequence[Status] = attr.ib(
        validator=no_duplicate_status, converter=convert_status_sequence
    )

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

    def to_value(self) -> str:
        return f"{self._label}{self._status_string}"

    def to_atf(self) -> str:
        return f"{self._atf}{self._status_string}"


@attr.s(auto_attribs=True, frozen=True)
class ColumnLabel(Label):

    column: int

    @staticmethod
    def from_label(column: str, status: Iterable[Status] = tuple()) -> "ColumnLabel":
        return ColumnLabel(status, roman.fromRoman(column.upper()))  # pyre-fixme[6]

    @staticmethod
    def from_int(column: int, status: Iterable[Status] = tuple()) -> "ColumnLabel":
        return ColumnLabel(status, column)  # pyre-fixme[6]

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
    text: str = attr.ib(default="")

    @text.validator
    def _check_text(self, attribute, value):
        if value and self.surface not in [
            Surface.SURFACE,
            Surface.FACE,
            Surface.EDGE,
        ]:
            raise ValueError(
                "text can only be initialized if atf.surface is 'SURFACE' or 'EDGE' or 'FACE'"
            )

    @staticmethod
    def from_label(
        surface: Surface, status: Iterable[Status] = tuple(), text: str = ""
    ) -> "SurfaceLabel":
        return SurfaceLabel(status, surface, text)  # pyre-fixme[6]

    @property
    def _label(self) -> str:
        return self.surface.label or ""

    @property
    def _atf(self) -> str:
        return f"@{self.surface.atf}"

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_surface_label(self)

    def to_atf(self) -> str:
        text = f" {self.text}" if self.text else ""
        return f"{self._atf}{self._status_string}{text}"


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
    string_from(*[surface.label for surface in Surface if surface.label])
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


def parse_label(label: str) -> Label:
    return LABEL.parse(label)
