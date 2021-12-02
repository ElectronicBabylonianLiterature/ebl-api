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

    def to_csv(self, separator: str) -> str:
        title = f"{self.a.name}{separator}{self.b.name}"
        return (
            "\n".join(
                separator.join(
                    map(
                        str,
                        [
                            title,
                            alignment.score,
                            round(alignment.percentPreservedIdentity(), 2),
                            round(alignment.percentPreservedSimilarity(), 2),
                        ],
                    )
                )
                for alignment in self.alignments
            )
            if self.alignments
            else f"{title}{separator}{self.score}{separator*2}"
        )
