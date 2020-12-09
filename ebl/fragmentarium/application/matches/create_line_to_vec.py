from enum import Enum
from functools import reduce, singledispatch
from typing import Sequence, Tuple

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine, StateDollarLine
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import (
    LineNumber,
    LineNumberRange,
    AbstractLineNumber,
)
from ebl.transliteration.domain.text_line import TextLine


class LineToVecEncoding(Enum):
    START = 0
    TEXT_LINE = 1
    SINGLE_RULING = 2
    DOUBLE_RULING = 3
    TRIPLE_RULING = 4
    END = 5

    @staticmethod
    def from_list(sequence: Sequence[int]) -> Tuple["LineToVecEncoding", ...]:
        return tuple(map(LineToVecEncoding, sequence))


LineToVecEncodings = Tuple[LineToVecEncoding, ...]


@singledispatch
def line_to_vec(line: Line, _: bool) -> LineToVecEncodings:
    return tuple()


@line_to_vec.register(TextLine)
def _line_to_vec_text(line: TextLine, first_line: bool) -> LineToVecEncodings:
    if first_line and not (
        line.line_number.has_prime  # pyre-ignore[16]
        or line.line_number.prefix_modifier  # pyre-ignore[16]
    ):
        return LineToVecEncoding.START, LineToVecEncoding.TEXT_LINE
    else:
        return (LineToVecEncoding.TEXT_LINE,)


@line_to_vec.register(RulingDollarLine)
def _line_to_vec_ruling(line: RulingDollarLine, _: bool) -> LineToVecEncodings:
    if line.number == atf.Ruling.SINGLE:
        return (LineToVecEncoding.SINGLE_RULING,)
    elif line.number == atf.Ruling.DOUBLE:
        return (LineToVecEncoding.DOUBLE_RULING,)
    elif line.number == atf.Ruling.TRIPLE:
        return (LineToVecEncoding.TRIPLE_RULING,)
    else:
        return tuple()


@line_to_vec.register(StateDollarLine)
def _line_to_vec_state(line: StateDollarLine, _: bool) -> LineToVecEncodings:
    if line.extent == atf.Extent.END_OF:
        return (LineToVecEncoding.END,)
    else:
        return tuple()


@singledispatch
def get_line_number(line_number: AbstractLineNumber) -> int:
    raise ValueError("No default for overloading")


@get_line_number.register(LineNumber)
def _get_line_number(line_number: LineNumber) -> int:
    return line_number.number


@get_line_number.register(LineNumberRange)
def _get_line_number_range(line_number: LineNumberRange) -> int:
    return line_number.end.number


@attr.s(auto_attribs=True, frozen=True)
class LineSplits:
    splits: Tuple[Tuple[Line, ...], ...] = (tuple(),)
    _last_line_number: int = -1

    @singledispatchmethod  # pyre-ignore[56]
    def add_line(self, line: Line) -> "LineSplits":
        return LineSplits(self._add_to_split(line), self._last_line_number)

    @add_line.register(TextLine)  # pyre-ignore[56]
    def _(self, line: TextLine) -> "LineSplits":
        current_line_number = get_line_number(line.line_number)
        splits = (
            self._open_split
            if self._last_line_number >= current_line_number
            else self._add_to_split
        )(line)
        return LineSplits(splits, current_line_number)

    def _open_split(self, line: Line) -> Tuple[Tuple[Line, ...], ...]:
        return (*self.splits, (line,))

    def _add_to_split(self, line: Line) -> Tuple[Tuple[Line, ...], ...]:
        past_splits = self.splits[:-1]
        current_split = self.splits[-1]
        return (*past_splits, (*current_split, line))


def split_lines(lines: Sequence[Line]) -> Tuple[Tuple[Line, ...], ...]:
    return reduce(
        lambda splits, line: splits.add_line(line), lines, LineSplits()
    ).splits


def create_line_to_vec(lines: Sequence[Line]) -> Tuple[LineToVecEncodings, ...]:
    list_of_lines = split_lines(lines)
    line_to_vec_result = []
    line_to_vec_intermediate_result = []
    for lines in list_of_lines:
        first_line = True
        for line in lines:
            line_to_vec_intermediate_result.extend(line_to_vec(line, first_line))
            first_line = False
        line_to_vec_result.append(tuple(line_to_vec_intermediate_result))
        line_to_vec_intermediate_result = []

    return tuple(line_to_vec_result) if len(line_to_vec_result[0]) else tuple()
