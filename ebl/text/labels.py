import attr
from parsy import (regex, char_from, string_from, seq)
import roman

from ebl.text.atf import Surface, LabelFlag


@attr.s(auto_attribs=True, frozen=True)
class ColumnLabel:
    column: int
    flag: LabelFlag = LabelFlag.NONE

    @staticmethod
    def from_label(column, flag=LabelFlag.NONE):
        return ColumnLabel(roman.fromRoman(column.upper()), flag)


@attr.s(auto_attribs=True, frozen=True)
class SurfaceLabel:
    surface: Surface
    flag: LabelFlag = LabelFlag.NONE


LABEL_FLAG = char_from(''.join(
    [flag.value for flag in LabelFlag if flag is not LabelFlag.NONE]
)).optional().map(
    lambda flag: LabelFlag(flag) if flag else LabelFlag.NONE
).desc('label flag')
SURFACE_LABEL = string_from(
    *[surface.label for surface in Surface]
).map(Surface.from_label).desc('surface label')
COLUMN_LABEL = regex(r'[ivx]+').desc('column label')
LABEL = (seq(SURFACE_LABEL, LABEL_FLAG).combine(SurfaceLabel) |
         seq(COLUMN_LABEL, LABEL_FLAG).combine(ColumnLabel.from_label))


def parse_label(string: str):
    return LABEL.parse(string)
