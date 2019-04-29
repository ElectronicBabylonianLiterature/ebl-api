from abc import ABC, abstractmethod

import attr
from parsy import (regex, char_from, string_from, seq)
import roman

from ebl.text.atf import Surface, Status


@attr.s(auto_attribs=True, frozen=True)
class Label(ABC):
    status: Status

    @property
    @abstractmethod
    def _label(self) -> str:
        ...

    @staticmethod
    def parse(string: str) -> 'Label':
        return LABEL.parse(string)

    def to_value(self) -> str:
        return f'{self._label}{self.status.value}'


@attr.s(auto_attribs=True, frozen=True)
class ColumnLabel(Label):
    """ See "Column" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    """

    column: int

    @staticmethod
    def from_label(column: str, flag: Status = Status.NONE) -> 'ColumnLabel':
        return ColumnLabel(flag, roman.fromRoman(column.upper()))

    @property
    def _label(self) -> str:
        return roman.toRoman(self.column).lower()


@attr.s(auto_attribs=True, frozen=True)
class SurfaceLabel(Label):

    surface: Surface

    @staticmethod
    def from_label(
            surface: Surface, flag: Status = Status.NONE
    ) -> 'SurfaceLabel':
        return SurfaceLabel(flag, surface)

    @property
    def _label(self) -> str:
        return self.surface.label


STATUS = char_from(''.join(
    [status.value for status in Status if status is not Status.NONE]
)).optional().map(
    lambda flag: Status(flag) if flag else Status.NONE
).desc('label flag')
SURFACE = string_from(
    *[surface.label for surface in Surface]
).map(Surface.from_label).desc('surface label')
COLUMN = regex(r'[ivx]+').desc('column label')
LABEL = (seq(SURFACE, STATUS).combine(SurfaceLabel.from_label) |
         seq(COLUMN, STATUS).combine(ColumnLabel.from_label))
