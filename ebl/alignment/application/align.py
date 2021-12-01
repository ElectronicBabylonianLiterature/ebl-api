from typing import List, Tuple

from alignment.sequencealigner import GlobalSequenceAligner  # pyre-ignore[21]
from alignment.vocabulary import Vocabulary  # pyre-ignore[21]

from ebl.alignment.domain.sequence import NamedSequence
from ebl.alignment.domain.scoring import EblScoring
from ebl.alignment.domain.result import AlignmentResult


def align_pair(
    first: NamedSequence,
    second: NamedSequence,
    vocabulary: Vocabulary,  # pyre-ignore[11]
) -> AlignmentResult:
    scoring = EblScoring(vocabulary)
    aligner = GlobalSequenceAligner(scoring, True)
    score, alignments = aligner.align(first.sequence, second.sequence, backtrace=True)
    return AlignmentResult(  # pyre-ignore[19]
        score,
        first,
        second,
        [vocabulary.decodeSequenceAlignment(encoded) for encoded in alignments],
    )


def align(
    pairs: List[Tuple[NamedSequence, NamedSequence]], vocabulary: Vocabulary
) -> str:
    results = [align_pair(first, second, vocabulary) for (first, second) in pairs]

    return "\n".join(
        result.to_csv()
        for result in sorted(results, key=lambda result: result.score, reverse=True)
    )
