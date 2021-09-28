import sys
import time
import re

from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import LocalSequenceAligner, GlobalSequenceAligner

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.ebl_scoring import EblScoring

sys.setrecursionlimit(50000)

minScore = 6
gapScore = -2
local = False

def align(pairs, v):
    no_alignment = []
    results = []
    x = 1

    for a,b in pairs:
        aEncoded = a[1]
        bEncoded = b[1]

        # Create a scoring and align the sequences using global aligner.
        scoring = EblScoring(v)
        aligner = (LocalSequenceAligner if local else GlobalSequenceAligner)(scoring, gapScore)
        score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

        if score > minScore and len(encodeds) > 0:
            results.append((x, a[0], b[0], score, encodeds))
        x += 1

    for result in sorted(
        results, key=lambda result: (result[4][0].percentIdentity(),result[4][0].score), reverse=True
    ):
        encodeds = result[4]
        alignments = [v.decodeSequenceAlignment(encoded) for encoded in encodeds]
        alignments = [
            alignment
            for alignment in alignments
            if not any([re.fullmatch(r"[X\s#\-]+", row) for row in str(alignment).split("\n")]) and alignment.score > minScore
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
