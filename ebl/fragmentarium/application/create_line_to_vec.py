from enum import Enum
from functools import singledispatch
from typing import Sequence, Optional, Tuple

import pydash  # pyre-ignore[21]

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine, StateDollarLine
from ebl.transliteration.domain.line import Line
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
def line_to_vec(line: Line, _: bool) -> Optional[LineToVecEncoding]:
    return None


@line_to_vec.register(TextLine)
def _line_to_vec_text(line: TextLine, first_line=True):
    if first_line and (
        line.line_number.has_prime  # pyre-ignore[16]
        or line.line_number.prefix_modifier  # pyre-ignore[16]
    ):
        return LineToVecEncoding.START, LineToVecEncoding.TEXT_LINE
    else:
        return LineToVecEncoding.TEXT_LINE


@line_to_vec.register(RulingDollarLine)
def _line_to_vec_ruling(line: RulingDollarLine, _: bool):
    if line.number == atf.Ruling.SINGLE:
        return LineToVecEncoding.SINGLE_RULING
    elif line.number == atf.Ruling.DOUBLE:
        return LineToVecEncoding.DOUBLE_RULING
    elif line.number == atf.Ruling.TRIPLE:
        return LineToVecEncoding.TRIPLE_RULING


@line_to_vec.register(StateDollarLine)
def _line_to_vec_state(line: StateDollarLine, _: bool):
    if line.extent == atf.Extent.END_OF:
        return LineToVecEncoding.END


def create_line_to_vec(lines: Sequence[Line]) -> LineToVecEncodings:
    line_to_vec_result = []
    first_line = True
    for line in lines:
        line_to_vec_encoding = line_to_vec(line, first_line)
        if line_to_vec_encoding:
            line_to_vec_result.append(line_to_vec_encoding)
        first_line = False

    return tuple(pydash.flatten(line_to_vec_result))
