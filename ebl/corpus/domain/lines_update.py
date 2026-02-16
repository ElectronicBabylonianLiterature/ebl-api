from typing import Mapping, Set, Sequence

import attr
from ebl.corpus.domain.line import Line


@attr.s(auto_attribs=True, frozen=True)
class LinesUpdate:
    new: Sequence[Line]
    deleted: Set[int]
    edited: Mapping[int, Line]
