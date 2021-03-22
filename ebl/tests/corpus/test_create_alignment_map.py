from typing import List, Optional

import pytest

from ebl.transliteration.domain.tokens import ValueToken
from ebl.corpus.domain.create_alignment_map import create_alignment_map


@pytest.mark.parametrize(  # pyre-ignore[56]
    "old,new,expected",
    [
        (["kur"], ["kur"], [0]),
        (["kur"], ["ra"], [0]),
        (["kur"], [], [None]),
        ([], ["kur"], []),
        (["kur"], ["kur", "ra"], [0]),
        (["kur"], ["ra", "kur"], [1]),
        (["kur", "ra"], ["kur", "pa", "ra"], [0, 2]),
        (["kur", "ra"], ["kur"], [0, None]),
        (["kur", "ra"], ["ra"], [None, 0]),
        (["kur", "pa", "ra"], ["kur", "ra"], [0, None, 1]),
        (["a", "b", "c"], ["d", "e", "f"], [0, 1, 2]),
        (["a", "b", "c", "d"], ["f", "g", "c", "h"], [0, 1, 2, 3]),
        (["a", "b", "c", "d"], ["e", "d"], [None, None, None, 1]),
        (["a", "b", "c", "d"], ["a", "e"], [0, None, None, None]),
        (["a", "b", "c", "d", "e"], ["a", "f", "e"], [0, None, None, None, 2]),
    ],
)
def test_create_alignment_map(
    old: List[str], new: List[str], expected: List[Optional[int]]
) -> None:
    assert (
        create_alignment_map(
            [ValueToken.of(value) for value in old],
            [ValueToken.of(value) for value in new],
        )
        == expected
    )
