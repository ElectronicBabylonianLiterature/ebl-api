from typing import Sequence

import attr

from ebl.corpus.domain.line import Line


@attr.s(frozen=True, auto_attribs=True)
class LinesPage:
    total: int
    offset: int
    limit: int
    lines: Sequence[Line]
