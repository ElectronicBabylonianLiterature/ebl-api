import pytest

from ebl.transliteration.domain.atf import to_sub_index, sub_index_to_int

SUB_INDICES = [
    (None, "ₓ"),
    (1, ""),
    (2, "₂"),
    (3, "₃"),
    (4, "₄"),
    (5, "₅"),
    (6, "₆"),
    (7, "₇"),
    (8, "₈"),
    (9, "₉"),
    (0, "₀"),
    (1024, "₁₀₂₄"),
]


@pytest.mark.parametrize("number,expected", SUB_INDICES)
def test_to_sub_index(number, expected):
    assert to_sub_index(number) == expected


@pytest.mark.parametrize("expected,sub_index,", [*SUB_INDICES, (1, "₁")])
def test_sub_index_to_int(sub_index, expected):
    assert sub_index_to_int(sub_index) == expected
