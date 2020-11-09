import pytest

from ebl.fragmentarium.matching_fragments.score import matching_subsequence


@pytest.mark.parametrize("seq1, seq2,  subsequence",[
    [(1,2,1), (1,2,1), 3],
])
def test_matching_subsequence(seq1, seq2, subsequence):
    assert matching_subsequence(seq1, seq2) ==  subsequence