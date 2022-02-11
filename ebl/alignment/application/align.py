from typing import List, Tuple

from alignment.sequencealigner import GlobalSequenceAligner
from alignment.vocabulary import Vocabulary

from ebl.alignment.domain.sequence import NamedSequence
from ebl.alignment.domain.scoring import EblScoring
from ebl.alignment.domain.result import AlignmentResult


def align_pair(
    first: NamedSequence,
    second: NamedSequence,
    vocabulary: Vocabulary,
) -> AlignmentResult:
    scoring = EblScoring(vocabulary)
    aligner = GlobalSequenceAligner(scoring, True)
    score, alignments = aligner.align(first.sequence, second.sequence, backtrace=True)
    return AlignmentResult(
        score,
        first,
        second,
        [vocabulary.decodeSequenceAlignment(encoded) for encoded in alignments],
    )


def align(
    pairs: List[Tuple[NamedSequence, NamedSequence]], vocabulary: Vocabulary
) -> List[AlignmentResult]:
    return sorted(
        (align_pair(first, second, vocabulary) for (first, second) in pairs),
        key=lambda result: result.score,
        reverse=True,
    )
