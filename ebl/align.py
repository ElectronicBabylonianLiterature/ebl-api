from ebl.corpus.domain.manuscript import Siglum
from typing import List, Tuple

from alignment.vocabulary import Vocabulary
from ebl.signs.infrastructure.menoizing_sign_repository import MemoizingSignRepository
from ebl.transliteration.domain.sign import Sign
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.app import create_context
import sys
import re
from collections import Counter

import pydash

from alignment.sequencealigner import (
    LocalSequenceAligner,
    GlobalSequenceAligner,
    SequenceAlignment,
)
from alignment.sequence import EncodedSequence, Sequence

from ebl.ebl_scoring import (
    EblScoring,
    gapScore,
    minScore,
    minIdentity,
    minSimilarity,
    identity_cutoff,
    curated_substitutions,
)

sys.setrecursionlimit(50000)


local = True

context = create_context()
signs_repository: SignRepository = MemoizingSignRepository(context.sign_repository)


def replace_line_breaks(string: str) -> str:
    return string.replace("\n", " # ").strip()


def collapse_spaces(string: str) -> str:
    return re.sub(r"\s+", " ", string).strip()


def make_sequence(string: str) -> Sequence:
    return Sequence(
        collapse_spaces(replace_line_breaks(string).replace("X", " ")).split(" ")
    )


def get_unicode(sign: Sign) -> List[str]:
    return (
        [chr(codepoint) for codepoint in sign.unicode] if sign.unicode else [sign.name]
    )


def map_sign(sign: str) -> str:
    match = re.match(r"(\D+)(\d+)", sign)
    signs = (
        signs_repository.search_by_lists_name(match.groups()[0], match.groups()[1])
        if match
        else []
    )
    if signs:
        unicodes = {unicode for s in signs for unicode in get_unicode(s)}
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


def print_counter(c: Counter) -> None:
    for cc, n in c.most_common():
        print(
            str(n).rjust(4),
            "\t\t",
            ", ".join(f"{sign} ({map_sign(sign)})" for sign in cc),
        )


def align(
    pairs: List[Tuple[Tuple[Siglum, EncodedSequence], Tuple[Siglum, EncodedSequence]]],
    v: Vocabulary,
    verbose: bool,
    key=lambda result: (result[4][0].percentIdentity(), result[4][0].score),
) -> Counter:
    substitutions = []
    results = []
    for x, (a, b) in enumerate(pairs, start=1):
        aEncoded = a[1]
        bEncoded = b[1]

        scoring = EblScoring(v)
        aligner = (LocalSequenceAligner if local else GlobalSequenceAligner)(
            scoring, gapScore
        )
        score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

        if score > minScore and len(encodeds) > 0:
            results.append((x, a[0], b[0], score, encodeds))

    for result in sorted(results, key=key, reverse=True):
        encodeds = result[4]
        alignments = [v.decodeSequenceAlignment(encoded) for encoded in encodeds]
        alignments = [
            alignment
            for alignment in alignments
            if not any(
                re.fullmatch(r"[X\s#\-]+", row)
                for row in str(alignment).split("\n")
            )
            and alignment.score >= minScore
            and alignment.percentIdentity() >= minIdentity
            and alignment.percentSimilarity() >= minSimilarity
        ]

        if alignments:
            print(f"{result[0]} -- {result[1]} vs {result[2]} ".ljust(80, "-"))

            for alignment in alignments:
                result = str(alignment)
                if verbose:
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
    uncurated_substitutions = [
        s for s in pure_substitutions if s not in curated_substitutions
    ]
    c = Counter(uncurated_substitutions)

    if verbose:
        print(80 * "=")
        print("Total pairs: ", len(substitutions))
        print("Total substitutions: ", len(pure_substitutions))
        print("Total unique substitutions: ", len(set(pure_substitutions)))
        print(
            "Total unique uncurated substitutions: ", len(set(uncurated_substitutions))
        )
        print_counter(c)

    return c
