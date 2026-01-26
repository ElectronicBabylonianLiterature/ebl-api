import itertools
from typing import List, Tuple

import pydash

from ebl.fragmentarium.domain.line_to_vec_encoding import (
    LineToVecEncoding,
    LineToVecEncodings,
)


def score(
    seq1: Tuple[LineToVecEncodings, ...], seq2: Tuple[LineToVecEncodings, ...]
) -> int:
    overlaps = list_of_overalps(seq1, seq2)
    return max(len(overlap) for overlap in overlaps) if len(overlaps) else 0


def score_weighted(
    seq1: Tuple[LineToVecEncodings, ...], seq2: Tuple[LineToVecEncodings, ...]
) -> int:
    overlaps = list_of_overalps(seq1, seq2)
    return weight_subsequence(overlaps) if len(overlaps) else 0


def list_of_overalps(
    seqs1: Tuple[LineToVecEncodings, ...], seqs2: Tuple[LineToVecEncodings, ...]
) -> List[LineToVecEncodings]:
    seqs1_backwards = tuple(seq[::-1] for seq in seqs1)
    seqs2_backwards = tuple(seq[::-1] for seq in seqs2)
    return pydash.flatten(
        [
            *compute_score_for_all(seqs1, seqs2),
            *compute_score_for_all(seqs1_backwards, seqs2_backwards),
        ]
    )


def compute_score_for_all(
    seqs1: Tuple[LineToVecEncodings, ...], seqs2: Tuple[LineToVecEncodings, ...]
) -> List[Tuple[LineToVecEncodings, ...]]:
    return [compute_score(seq1, seq2) for seq1, seq2 in itertools.product(seqs1, seqs2)]


def compute_score(
    seq1: LineToVecEncodings, seq2: LineToVecEncodings
) -> Tuple[LineToVecEncodings, ...]:
    shorter_seq, longer_seq = sorted((seq1, seq2), key=len)
    return tuple(
        shorter_seq[-i:]
        for i in range(1, len(longer_seq) + 1)
        if (
            i >= len(shorter_seq)
            and longer_seq[i - len(shorter_seq) : i] == shorter_seq[-i:]
        )
        or longer_seq[:i] == shorter_seq[-i:]
    )


def weight_subsequence(seq_of_seq: List[LineToVecEncodings]) -> int:
    weighting = {
        LineToVecEncoding.START: 3,
        LineToVecEncoding.TEXT_LINE: 1,
        LineToVecEncoding.SINGLE_RULING: 3,
        LineToVecEncoding.DOUBLE_RULING: 6,
        LineToVecEncoding.TRIPLE_RULING: 10,
        LineToVecEncoding.END: 3,
    }
    return max(
        sum(elem)
        for elem in [[weighting[number] for number in seq] for seq in seq_of_seq]
    )
