import pytest

from ebl.fragmentarium.matching_fragments.score import matching_subseq, matching_subseq_w


@pytest.mark.parametrize("seq1, seq2,  score_, score_weighted",[
    [(1, 2, 1), (1, 2, 1), 3, 5],
    [(1, 2, 1, 1, 5), (0, 1, 2, 1, 1, 5), 5, 9],
    [(1, 2, 1, 1, 5), (1, 2, 1, 1, 1, 1, 1, 5), 0, 0],
    [(5, 1, 1, 2, 1), (5, 1, 1, 1, 1, 1, 2, 1), 0, 0],
    [(0, 1, 1, 2, 1), (1, 2, 1, 1, 1, 1, 1, 5), 3, 5],
    [(0, 1, 1, 1, 1), (1, 2, 1, 1, 1, 1, 1, 5), 1, 0],
    [(1, 1, 2, 1, 1), (2, 1, 2, 1, 1), 2, 0],
    [(1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 3, 1, 1, 1, 1),
     (1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 5, 1, 1), 1, 0],
    [(0, 1, 1, 2), (1, 1, 2, 1), 3, 5],
    [(1, 1, 2, 5), (1, 1, 2, 1), 1, 0],
    [(0, 1, 1, 2, 5), (1, 1, 2), 3, 5],
    [(0, 1, 1, 2, 5), (1, 1, 2, 1), 0, 0]
])
def test_matching_subsequence(seq1, seq2, score_, score_weighted):
    assert matching_subseq(seq1, seq2) == score_
    assert matching_subseq_w(seq1, seq2) == score_weighted
