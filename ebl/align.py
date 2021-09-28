from typing import List
from ebl.signs.infrastructure.menoizing_sign_repository import MemoizingSignRepository
from ebl.transliteration.domain.sign import Sign
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.app import create_context
import sys
import re
from collections import Counter

import pydash

from alignment.sequencealigner import LocalSequenceAligner, GlobalSequenceAligner, SequenceAlignment
from alignment.sequence import Sequence

from ebl.ebl_scoring import EblScoring

sys.setrecursionlimit(50000)

identity_cutoff = 80
minScore = 3
gapScore = -2  
local = True

context = create_context()
signs_repository: SignRepository = MemoizingSignRepository(context.sign_repository)


def make_sequence(string: str) -> Sequence:
    return Sequence(re.sub(" +", " ", string.replace("\n", " # ").replace("X", " ")).strip().split(" "))


def get_unicode(sign: Sign) -> List[str]:
    return [chr(codepoint) for codepoint in sign.unicode] if sign.unicode else [sign.name]

def map_sign(sign: str) -> str:
    match = re.match(r"(\D+)(\d+)", sign)
    signs = signs_repository.search_by_lists_name(match.groups()[0], match.groups()[1]) if match else []
    if signs:
        unicodes = {
            unicode
            for s in signs
            for unicode in get_unicode(s) 
        }
        return "|".join(sorted(unicodes))
    else:
        return sign

def to_unicode_signs(alignment: SequenceAlignment) -> str:
    lines = [
        [map_sign(sign) for sign in line.split(" ")]
        for line in str(alignment).split("\n")
    ]
    pairs = pydash.zip_(lines[0], lines[1])
    
    line0 = []
    line1 = []
    for pair in pairs:
        length = max(len(pair[0]), len(pair[1]))
        line0.append(pair[0].ljust(length))
        line1.append(pair[1].ljust(length))


    return "\t".join(line0) + "\n" + "\t".join(line1)


def align(pairs, v):
    substitutions = []
    results = []
    x = 1

    for a, b in pairs:
        aEncoded = a[1]
        bEncoded = b[1]

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
                result = str(alignment)  # to_unicode_signs(alignment)
                print(result)
                print("Alignment score:", alignment.score)
                print("Percent identity:", alignment.percentIdentity())
                print("Percent similarity:", alignment.percentSimilarity())
                print()

                if alignment.percentIdentity() >= identity_cutoff:
                    lines = [re.split(r"\s+", line) for line in result.split("\n")]
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
        print(str(n).rjust(4), "\t\t",", ".join(
            f"{sign} ({map_sign(sign)})"
            for sign in cc
        ))
