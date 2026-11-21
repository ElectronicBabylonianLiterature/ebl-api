from typing import Sequence

import attr

from ebl.corpus.domain.line import Line


@attr.s(auto_attribs=True, frozen=True)
class LineMove:
    source: int
    target: int

    def apply(self, lines: Sequence[Line]) -> Sequence[Line]:
        self._validate(len(lines))
        reordered = [line for index, line in enumerate(lines) if index != self.source]
        reordered.insert(self.target, lines[self.source])
        return tuple(reordered)

    def _validate(self, line_count: int) -> None:
        for name, position in (("from", self.source), ("to", self.target)):
            if not 0 <= position < line_count:
                raise ValueError(
                    f"Invalid line move: {name} {position} is not a line position "
                    f"(number of lines: {line_count})."
                )
        if self.source == self.target:
            raise ValueError("Invalid line move: the line is already at that position.")
