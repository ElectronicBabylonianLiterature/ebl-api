import pytest  # pyre-ignore[16

from ebl.fragmentarium.application.matches.create_line_to_vec import LineToVecEncoding
from ebl.fragmentarium.application.matches.line_to_vec_score import score, score_weighted


@pytest.mark.parametrize(
    "seq1, seq2,  unweighted_score, weighted_score",
    [
        [(1, 2, 1), (1, 2, 1), 3, 3],
        [(1, 2, 1, 1, 5), (0, 1, 2, 1, 1, 5), 5, 6],
        [(1, 2, 1, 1, 5), (1, 2, 1, 1, 1, 1, 1, 5), 0, 0],
        [(5, 1, 1, 2, 1), (5, 1, 1, 1, 1, 1, 2, 1), 0, 0],
        [(0, 1, 1, 2, 1), (1, 2, 1, 1, 1, 1, 1, 5), 3, 3],
        [(0, 1, 1, 1, 1), (1, 2, 1, 1, 1, 1, 1, 5), 1, 0],
        [(1, 1, 2, 1, 1), (2, 1, 2, 1, 1), 2, 0],
        [
            (1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 3, 1, 1, 1, 1),
            (1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 5, 1, 1),
            1,
            0,
        ],
        [(0, 1, 1, 2), (1, 1, 2, 1), 3, 3],
        [(1, 1, 2, 5), (1, 1, 2, 1), 1, 0],
        [(0, 1, 1, 2, 5), (1, 1, 2), 3, 3],
        [(0, 1, 1, 2, 5), (1, 1, 2, 1), 0, 0],
    ],
)
def test_matching_subsequence(seq1, seq2, unweighted_score, weighted_score):
    seq1 = LineToVecEncoding.from_list(seq1)
    seq2 = LineToVecEncoding.from_list(seq2)
    assert score(seq1, seq2) == unweighted_score
    assert score_weighted(seq1, seq2) == weighted_score
