from typing import Callable, List, Tuple, Union

from alignment.sequencealigner import GlobalSequenceAligner  # pyre-ignore[21]
from alignment.vocabulary import Vocabulary  # pyre-ignore[21]

from ebl.alignment.domain.sequence import NamedSequence
from ebl.alignment.domain.scoring import EblScoring
from ebl.alignment.domain.result import AlignmentResult


def align_pair(
    a: NamedSequence, b: NamedSequence, v: Vocabulary  # pyre-ignore[11]
) -> AlignmentResult:
    scoring = EblScoring(v)
    aligner = GlobalSequenceAligner(scoring, True)
    score, alignments = aligner.align(a.sequence, b.sequence, backtrace=True)
    return AlignmentResult(  # pyre-ignore[19]
        score, a, b, [v.decodeSequenceAlignment(encoded) for encoded in alignments]
    )


def default_key(result: AlignmentResult) -> Tuple[Union[int, float], ...]:
    return (
        (result.alignments[0].percentPreservedIdentity(), result.alignments[0].score)
        if result.alignments
        else (0, 0, result.score)
    )


def align(
    pairs: List[Tuple[NamedSequence, NamedSequence]],
    v: Vocabulary,
    key: Callable[
        [AlignmentResult], Union[int, float, Tuple[Union[int, float], ...]]
    ] = default_key,
) -> str:
    results = [align_pair(a, b, v) for (a, b) in pairs]

    return "\n".join(
        result.to_csv() for result in sorted(results, key=key, reverse=True)
    )
