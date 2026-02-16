from typing import Sequence

import attr

from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.line_number import AbstractLineNumber


@attr.s(auto_attribs=True, frozen=True)
class ExtantLine:
    label: Sequence[Label]
    line_number: AbstractLineNumber
    is_side_boundary: bool

    @staticmethod
    def of(line: Line, manuscript_id: int) -> "ExtantLine":
        manuscript_line = line.get_manuscript_line(manuscript_id)
        return ExtantLine(
            manuscript_line.labels,
            line.number,
            manuscript_line.is_beginning_of_side or manuscript_line.is_end_of_side,
        )
