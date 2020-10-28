import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Iterable, Sequence, Tuple, Union

import attr
import roman  # pyre-ignore[21]
from lark.lexer import Token  # pyre-ignore[21]
from lark.visitors import Transformer, v_args  # pyre-ignore[21]
from lark.lark import Lark  # pyre-ignore[21]

from ebl.transliteration.domain.atf import Object, Status, Surface


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
    def visit_object_label(self, label: "ObjectLabel") -> "LabelVisitor":
        ...


def no_duplicate_status(_instance, _attribute, value) -> None:
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
    def abbreviation(self) -> str:
        ...

    @property
    @abstractmethod
    def _atf(self) -> str:
        ...

    @property
    def status_string(self) -> str:
        return "".join([status.value for status in self.status])

    @abstractmethod
    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        ...

    def to_value(self) -> str:
        return f"{self.abbreviation}{self.status_string}"

    def to_atf(self) -> str:
        return f"{self._atf}{self.status_string}"


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
    def abbreviation(self) -> str:
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
    def _check_text(self, attribute, value) -> None:
        if value and self.surface not in [Surface.SURFACE, Surface.FACE, Surface.EDGE]:
            raise ValueError(
                "Non-empty text is only allowed for SURFACE, EDGE or FACE."
            )

    @staticmethod
    def from_label(
        surface: Surface, status: Iterable[Status] = tuple(), text: str = ""
    ) -> "SurfaceLabel":
        return SurfaceLabel(status, surface, text)  # pyre-fixme[6]

    @property
    def abbreviation(self) -> str:
        return (
            self.text or self.surface.label or ""
            if self.surface == Surface.EDGE
            else self.surface.label or self.text
        )

    @property
    def _atf(self) -> str:
        return f"@{self.surface.atf}"

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_surface_label(self)

    def to_atf(self) -> str:
        text = f" {self.text}" if self.text else ""
        return f"{self._atf}{self.status_string}{text}"


@attr.s(auto_attribs=True, frozen=True)
class ObjectLabel(Label):

    object: Object
    text: str = attr.ib(default="")

    @text.validator
    def _check_text(self, attribute, value) -> None:
        if value and self.object not in [Object.OBJECT, Object.FRAGMENT]:
            raise ValueError("Non-empty text is only allowed for OBJECT and FRAGMENT.")

    @property
    def abbreviation(self) -> str:
        return self.text or self.object.value

    @property
    def _atf(self) -> str:
        return f"@{self.object.value}"

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_object_label(self)

    def to_atf(self) -> str:
        text = f" {self.text}" if self.text else ""
        return f"{self._atf}{self.status_string}{text}"


LINE_NUMBER_EXPRESSION = r"[^\s]+"


def is_sequence_of_non_space_characters(_instance, _attribute, value) -> None:
    if not re.fullmatch(LINE_NUMBER_EXPRESSION, value):
        raise ValueError(
            f'Line number "{value}" is not a sequence of ' "non-space characters."
        )


class LabelTransformer(Transformer):  # pyre-ignore[11]
    @v_args(inline=True)  # pyre-ignore[56]
    def column_label(
        self, numeral: Token, status: Sequence[Status]  # pyre-ignore[11]
    ) -> ColumnLabel:
        return ColumnLabel.from_label(numeral, status)

    @v_args(inline=True)  # pyre-ignore[56]
    def surface_label(self, surface: Surface, status: Sequence[Status]) -> SurfaceLabel:
        return SurfaceLabel.from_label(surface, status)

    @v_args(inline=True)  # pyre-ignore[56]
    def surface(self, surface: Token) -> Surface:
        return Surface.from_label(surface)

    def status(self, children: Iterable[Token]) -> Sequence[Status]:
        return tuple(Status(token) for token in children)


LABEL_PARSER = Lark.open("labels.lark", maybe_placeholders=True, rel_to=__file__)


def parse_label(label: str) -> Label:
    tree = LABEL_PARSER.parse(label)
    return LabelTransformer().transform(tree)  # pyre-ignore[16]
