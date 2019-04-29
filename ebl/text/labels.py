import attr
from parsy import (regex, char_from, string_from, seq)
import roman

from ebl.text.atf import Surface, Status


@attr.s(auto_attribs=True, frozen=True)
class ColumnLabel:
    """ See "Column" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    """

    column: int
    status: Status = Status.NONE

    @staticmethod
    def from_label(column, flag=Status.NONE):
        return ColumnLabel(roman.fromRoman(column.upper()), flag)

    def to_value(self) -> str:
        roman_column = roman.toRoman(self.column).lower()
        return f'{roman_column}{self.status.value}'


@attr.s(auto_attribs=True, frozen=True)
class SurfaceLabel:
    # pylint: disable=R0903

    surface: Surface
    status: Status = Status.NONE

    def to_value(self) -> str:
        return f'{self.surface.label}{self.status.value}'


STATUS = char_from(''.join(
    [status.value for status in Status if status is not Status.NONE]
)).optional().map(
    lambda flag: Status(flag) if flag else Status.NONE
).desc('label flag')
SURFACE = string_from(
    *[surface.label for surface in Surface]
).map(Surface.from_label).desc('surface label')
COLUMN = regex(r'[ivx]+').desc('column label')
LABEL = (seq(SURFACE, STATUS).combine(SurfaceLabel) |
         seq(COLUMN, STATUS).combine(ColumnLabel.from_label))


def parse_label(string: str):
    return LABEL.parse(string)
