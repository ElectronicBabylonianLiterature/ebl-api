import sys
import re
from collections import Counter
from typing import Sequence

import pydash

from alignment.sequencealigner import LocalSequenceAligner, GlobalSequenceAligner

from ebl.ebl_scoring import EblScoring

sys.setrecursionlimit(50000)


def make_sequence(string: str) -> Sequence:
    return Sequence(re.sub(" +", " ", string.replace("\n", " # ").replace("X", " ")).strip().split(" "))


minScore = 3
gapScore = -2
local = False


def align(pairs, v):
    substitutions = []
    results = []
    x = 1

    for a, b in pairs:
        aEncoded = a[1]
        bEncoded = b[1]

        # Create a scoring and align the sequences using global aligner.
        scoring = EblScoring(v)
        aligner = (LocalSequenceAligner if local else GlobalSequenceAligner)(
            scoring, gapScore
        )
        score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

        if score > minScore and len(encodeds) > 0:
            results.append((x, a[0], b[0], score, encodeds))
        x += 1

    for result in sorted(
        results,
        key=lambda result: (result[4][0].percentIdentity(), result[4][0].score),
        reverse=True,
    ):
        encodeds = result[4]
        alignments = [v.decodeSequenceAlignment(encoded) for encoded in encodeds]
        alignments = [
            alignment
            for alignment in alignments
            if not any(
                [re.fullmatch(r"[X\s#\-]+", row) for row in str(alignment).split("\n")]
            )
            and alignment.score > minScore
        ]
        if alignments:
            print(
                f"\n{result[0]} == {result[1]} vs {result[2]} ============================================="
            )

            for alignment in alignments:
                print(alignment)
                print("Alignment score:", alignment.score)
                print("Percent identity:", alignment.percentIdentity())
                print("Percent similarity:", alignment.percentSimilarity())
                print()

                lines = [re.split(r"\s+", line) for line in str(alignment).split("\n")]
                pairs = pydash.zip_(lines[0], lines[1])
                pairs = [
                    frozenset(pair)
                    for pair in pairs
                    if "#" not in pair and "-" not in pair and "X" not in pair
                ]
                substitutions.extend(pairs)

    pure_substitutions = [s for s in substitutions if len(s) == 2]
    print("\n\n=====================================")
    print("\nTotal pairs: ", len(substitutions))
    print("Total substitutions: ", len(pure_substitutions))
    print("Total unique substitutions: ", len(set(pure_substitutions)))

    c = Counter(pure_substitutions)
    for cc, n in c.most_common():
        print(", ".join(cc), "\t\t\t\t", n)
