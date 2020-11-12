import pytest  # pyre-ignore[16

from ebl.fragmentarium.matching_fragments.score import score, score_weighted


@pytest.mark.parametrize(
    "seq1, seq2,  unweighted_score, weighted_score",
    [
        [(1, 2, 1), (1, 2, 1), 3, 5],
        [(1, 2, 1, 1, 5), (0, 1, 2, 1, 1, 5), 5, 9],
        [(1, 2, 1, 1, 5), (1, 2, 1, 1, 1, 1, 1, 5), 0, 0],
        [(5, 1, 1, 2, 1), (5, 1, 1, 1, 1, 1, 2, 1), 0, 0],
        [(0, 1, 1, 2, 1), (1, 2, 1, 1, 1, 1, 1, 5), 3, 5],
        [(0, 1, 1, 1, 1), (1, 2, 1, 1, 1, 1, 1, 5), 1, 0],
        [(1, 1, 2, 1, 1), (2, 1, 2, 1, 1), 2, 0],
        [
            (1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 3, 1, 1, 1, 1),
            (1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 5, 1, 1),
            1,
            0,
        ],
        [(0, 1, 1, 2), (1, 1, 2, 1), 3, 5],
        [(1, 1, 2, 5), (1, 1, 2, 1), 1, 0],
        [(0, 1, 1, 2, 5), (1, 1, 2), 3, 5],
        [(0, 1, 1, 2, 5), (1, 1, 2, 1), 0, 0],
    ],
)
def test_matching_subsequence(seq1, seq2, unweighted_score, weighted_score):
    assert score(seq1, seq2) == unweighted_score
    assert score_weighted(seq1, seq2) == weighted_score
