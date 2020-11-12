from typing import Sequence, Tuple

from ebl.transliteration.domain import atf
from ebl.transliteration.domain import text_line, dollar_line
from ebl.transliteration.domain.line import Line


def create_line_to_vec(lines: Sequence[Line]) -> Tuple[int, ...]:
    line_to_vec = []
    first_line = True
    for line in lines:
        if isinstance(line, text_line.TextLine):
            if first_line and (
                line.line_number.has_prime
                or line.line_number.prefix_modifier  # pyre-ignore[16]
            ):
                line_to_vec.append(0)
                line_to_vec.append(1)
                first_line = False
            else:
                line_to_vec.append(1)
                first_line = False
        elif isinstance(line, dollar_line.RulingDollarLine):
            if line.number == atf.Ruling.SINGLE:
                line_to_vec.append(2)
            elif line.number == atf.Ruling.DOUBLE:
                line_to_vec.append(3)
            elif line.number == atf.Ruling.TRIPLE:
                line_to_vec.append(4)
        elif (
            isinstance(line, dollar_line.StateDollarLine)
            and line.extent == atf.Extent.END_OF
        ):
            line_to_vec.append(5)
    return tuple(line_to_vec)
