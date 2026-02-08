import pytest

from ebl.fragmentarium.application.matches.line_to_vec_score import (
    score,
    score_weighted,
)
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding


@pytest.mark.parametrize(
    "seq1, seq2,  unweighted_score",
    [
        [((1, 2, 1),), ((1, 2, 1),), 3],
        [((1, 2, 1),), ((),), 0],
        [((1, 2, 1),), ((2, 1, 2),), 2],
        [((1, 2, 1),), ((2, 2, 1),), 1],
        [((1, 2, 1),), ((1, 2, 2),), 1],
        [((1, 2, 1),), ((2, 2, 2),), 0],
        [((1, 2, 1),), ((2, 2, 2), (1, 2, 1)), 3],
        [((1, 2, 1),), ((1, 2, 1), (2, 2, 2)), 3],
        [((2, 2, 2), (1, 2, 1)), ((1, 2, 1),), 3],
        [((1, 2, 1), (2, 2, 2)), ((1, 2, 1),), 3],
        [((1, 1, 2, 1, 1),), ((1, 2, 1),), 3],
        [((0, 1, 2, 1, 1),), ((1, 2, 5),), 1],
        [((0, 1, 2, 1), (1, 2, 1, 5)), ((2, 3, 2), (1, 1, 2, 1)), 3],
    ],
)
def test_score(seq1, seq2, unweighted_score):
    seq1 = tuple(map(LineToVecEncoding.from_list, seq1))
    seq2 = tuple(map(LineToVecEncoding.from_list, seq2))
    assert score(seq1, seq2) == unweighted_score


@pytest.mark.parametrize(
    "seq1, seq2,  weighted_score",
    [
        [((1, 2, 1),), ((1, 2, 1),), 5],
        [((1, 2, 1),), ((),), 0],
        [((1, 2, 1),), ((2, 1, 2),), 4],
        [((1, 2, 1),), ((2, 2, 1),), 1],
        [((1, 2, 1),), ((1, 2, 2),), 1],
        [((1, 2, 1),), ((2, 2, 2),), 0],
        [((1, 2, 1),), ((2, 2, 2), (1, 2, 1)), 5],
        [((1, 2, 1),), ((1, 2, 1), (2, 2, 2)), 5],
        [((2, 2, 2), (1, 2, 1)), ((1, 2, 1),), 5],
        [((1, 2, 1), (2, 2, 2)), ((1, 2, 1),), 5],
        [((1, 1, 2, 1, 1),), ((1, 2, 1),), 5],
        [((0, 1, 2, 1, 1),), ((1, 2, 5),), 1],
        [((0, 1, 2, 1), (1, 2, 1, 5)), ((2, 3, 2), (1, 1, 2, 1)), 5],
    ],
)
def test_weighted_score(seq1, seq2, weighted_score):
    seq1 = tuple(map(LineToVecEncoding.from_list, seq1))
    seq2 = tuple(map(LineToVecEncoding.from_list, seq2))
    assert score_weighted(seq1, seq2) == weighted_score


def test_matching_subsequence_itself():
    seq1 = tuple(
        map(
            LineToVecEncoding.from_list,
            [[1, 1, 1, 1, 1, 1, 1, 2], [0, 1, 1, 1, 1, 1, 1, 1]],
        )
    )
    seq2 = tuple(
        map(
            LineToVecEncoding.from_list,
            [[1, 1, 1, 1, 1], [0, 1, 1, 1, 1, 1, 1, 1, 1, 1]],
        )
    )

    assert score(seq1, seq1) >= score(seq1, seq2)
