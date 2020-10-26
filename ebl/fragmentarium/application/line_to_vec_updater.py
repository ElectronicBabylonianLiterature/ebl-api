from typing import Sequence
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain import text_line, dollar_line
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line_number import LineNumber


def create_line_to_vec(lines: Sequence[Line]) -> Sequence[int]:
    line_to_vec = []
    for line in lines:
        if isinstance(line, text_line.TextLine):
            if isinstance(line.line_number, LineNumber):
                if line.line_number.has_prime:  # pyre-ignore[16]
                    line_to_vec.append(1)
            else:
                line_to_vec.append(0)
        elif isinstance(line, dollar_line.RulingDollarLine):
            if line.number == atf.Ruling.SINGLE:
                line_to_vec.append(2)
            elif line.number == atf.Ruling.DOUBLE:
                line_to_vec.append(3)
            elif line.number == atf.Ruling.TRIPLE:
                line_to_vec.append(4)
        elif isinstance(line, dollar_line.StateDollarLine):
            if line.extent == atf.Extent.END_OF:
                line_to_vec.append(5)
    return tuple(line_to_vec)
