from typing import Mapping, Sequence, Set

import attr

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_layout import LineLayout


@attr.s(auto_attribs=True, frozen=True)
class LinesUpdate:
    new: Sequence[Line]
    deleted: Set[int]
    edited: Mapping[int, Line]

    def find_kept(self, line_count: int) -> Sequence[int]:
        return [
            index
            for index in range(line_count)
            if index in self.edited or index not in self.deleted
        ]

    def create_layout(self, line_count: int) -> LineLayout:
        return LineLayout.of_sources(self.find_kept(line_count), len(self.new))
