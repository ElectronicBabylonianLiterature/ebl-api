from typing import List

import attr
from alignment.sequencealigner import SequenceAlignment  # pyre-ignore[21]

from ebl.alignment.domain.sequence import NamedSequence


@attr.s(auto_attribs=True, frozen=True)
class AlignmentResult:
    score: int
    a: NamedSequence
    b: NamedSequence
    alignments: List[SequenceAlignment]  # pyre-ignore[11]

    @property
    def title(self) -> str:
        return f"{self.a.name}, {self.b.name}"

    def to_csv(self) -> str:
        return (
            "\n".join(
                f"{self.title}, {alignment.score}, "
                f"{round(alignment.percentPreservedIdentity(), 2)}, "
                f"{round(alignment.percentPreservedSimilarity(), 2)}"
                for alignment in self.alignments
            )
            if self.alignments
            else f"{self.title}, {self.score}, , "
        )
