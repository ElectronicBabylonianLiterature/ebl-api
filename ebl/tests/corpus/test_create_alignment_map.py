from typing import List

import pytest

from ebl.corpus.domain.create_alignment_map import AlignmentMap, create_alignment_map
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Caesura
from ebl.transliteration.domain.tokens import Token, ValueToken


def _make_sequence(values: List[str]) -> List[Token]:
    return [AkkadianWord.of((ValueToken.of(value),)) for value in values]


@pytest.mark.parametrize(
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
    old: List[str], new: List[str], expected: AlignmentMap
) -> None:
    assert create_alignment_map(_make_sequence(old), _make_sequence(new)) == expected


def test_create_alignment_map_remove_unalignable() -> None:
    assert create_alignment_map(_make_sequence(["kur"]), [Caesura.certain()]) == [None]
