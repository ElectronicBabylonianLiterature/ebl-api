from typing import List

import attr
from alignment.sequencealigner import SequenceAlignment

from ebl.alignment.domain.sequence import NamedSequence


@attr.s(auto_attribs=True, frozen=True)
class AlignmentResult:
    score: int
    a: NamedSequence
    b: NamedSequence
    alignments: List[SequenceAlignment]
