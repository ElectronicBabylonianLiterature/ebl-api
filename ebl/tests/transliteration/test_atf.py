import pytest

from ebl.transliteration.domain.atf import (
    AtfSyntaxError,
    to_sub_index,
    validate_atf,
    AtfError,
    sub_index_to_int,
)


def test_valid_atf():
    validate_atf("1. foo")


def test_invalid_atf():
    with pytest.raises(AtfSyntaxError, match="Line 1 is invalid.") as excinfo:
        validate_atf("$ this is not valid")

    assert excinfo.value.line_number == 1


def test_pyoracc_error():
    with pytest.raises(AtfError, match="Pyoracc validation failed: 'Single'."):
        validate_atf("$ Single ruling")


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


@pytest.mark.parametrize(
    "number,expected", SUB_INDICES,
)
def test_to_sub_index(number, expected):
    assert to_sub_index(number) == expected


@pytest.mark.parametrize(
    "expected,sub_index,", [*SUB_INDICES, (1, "₁")],
)
def test_sub_index_to_int(sub_index, expected):
    assert sub_index_to_int(sub_index) == expected
