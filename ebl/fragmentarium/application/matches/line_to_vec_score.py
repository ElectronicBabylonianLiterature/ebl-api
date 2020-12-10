from typing import List, Dict, Optional

from ebl.fragmentarium.application.matches.create_line_to_vec import (
    LineToVecEncodings,
    LineToVecEncoding,
)


def score_weighted(
    seq1: LineToVecEncodings,
    seq2: LineToVecEncodings,
    weights: Optional[Dict[LineToVecEncoding, int]] = None,
) -> int:
    matching_seq = feed_compute_score(seq1, seq2)
    matching_seq = [seq for seq in matching_seq if list(filter(lambda x: x != 1, seq))]
    if len(matching_seq) and all(matching_seq):
        return weight_subsequence(matching_seq, weights)
    else:
        return 0


def score(seq1: LineToVecEncodings, seq2: LineToVecEncodings) -> int:
    matching_seq = feed_compute_score(seq1, seq2)
    return max([len(x) for x in matching_seq]) if len(matching_seq) else 0


def feed_compute_score(
    seq1: LineToVecEncodings, seq2: LineToVecEncodings
) -> List[LineToVecEncodings]:
    return [*compute_score(seq1[::-1], seq2[::-1]), *compute_score(seq1, seq2)]


def compute_score(
    seq1: LineToVecEncodings, seq2: LineToVecEncodings
) -> List[LineToVecEncodings]:
    shorter_seq, longer_seq = sorted((seq1, seq2), key=len)
    matching_subseq = []
    for i in range(1, len(longer_seq) + 1):
        if (
            i >= len(shorter_seq)
            and longer_seq[i - len(shorter_seq) : i] == shorter_seq[-i:]
        ) or longer_seq[:i] == shorter_seq[-i:]:
            matching_subseq.append(shorter_seq[-i:])
    return matching_subseq


def weight_subsequence(
    seq_of_seq: List[LineToVecEncodings],
    weights: Optional[Dict[LineToVecEncoding, int]] = None,
) -> int:
    if weights:
        weighting = weights
    else:
        weighting = {
            LineToVecEncoding.START: 3,
            LineToVecEncoding.TEXT_LINE: 0,
            LineToVecEncoding.SINGLE_RULING: 3,
            LineToVecEncoding.DOUBLE_RULING: 6,
            LineToVecEncoding.TRIPLE_RULING: 10,
            LineToVecEncoding.END: 3,
        }
    return max(
        sum(elem)
        for elem in [[weighting[number] for number in seq] for seq in seq_of_seq]
    )
