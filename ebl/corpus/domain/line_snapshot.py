from typing import Optional, Sequence

import attr

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript import Manuscript


@attr.s(frozen=True, auto_attribs=True)
class LineSnapshot:
    line: Optional[Line]
    line_count: int
    manuscripts: Sequence[Manuscript]
    revision: str
