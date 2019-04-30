from abc import ABC, abstractmethod
from typing import Tuple, Iterable

import attr
from parsy import (regex, char_from, string_from, seq)
import roman

from ebl.text.atf import Surface, Status


class LabelVisitor(ABC):
    @abstractmethod
    def visit_surface_label(self, label: 'SurfaceLabel') -> 'LabelVisitor':
        ...

    @abstractmethod
    def visit_column_label(self, label: 'ColumnLabel') -> 'LabelVisitor':
        ...


@attr.s(auto_attribs=True, frozen=True)
class Label(ABC):
    status: Tuple[Status, ...]

    @property
    @abstractmethod
    def _label(self) -> str:
        ...

    @abstractmethod
    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        ...

    @staticmethod
    def parse(string: str) -> 'Label':
        return LABEL.parse(string)

    def to_value(self) -> str:
        status_value = ''.join([status.value for status in self.status])
        return f'{self._label}{status_value}'


@attr.s(auto_attribs=True, frozen=True)
class ColumnLabel(Label):
    """ See "Column" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    """

    column: int

    @staticmethod
    def from_label(column: str,
                   status: Iterable[Status] = tuple()) -> 'ColumnLabel':
        return ColumnLabel(tuple(status), roman.fromRoman(column.upper()))

    @property
    def _label(self) -> str:
        return roman.toRoman(self.column).lower()

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_column_label(self)


@attr.s(auto_attribs=True, frozen=True)
class SurfaceLabel(Label):

    surface: Surface

    @staticmethod
    def from_label(surface: Surface,
                   status: Iterable[Status] = tuple()) -> 'SurfaceLabel':
        return SurfaceLabel(tuple(status), surface)

    @property
    def _label(self) -> str:
        return self.surface.label

    def accept(self, visitor: LabelVisitor) -> LabelVisitor:
        return visitor.visit_surface_label(self)


STATUS = char_from(
    ''.join([status.value for status in Status])
).map(Status).desc('label status')
SURFACE = string_from(
    *[surface.label for surface in Surface]
).map(Surface.from_label).desc('surface label')
COLUMN = regex(r'[ivx]+').desc('column label')
LABEL = (seq(SURFACE, STATUS.many()).combine(SurfaceLabel.from_label) |
         seq(COLUMN, STATUS.many()).combine(ColumnLabel.from_label))
