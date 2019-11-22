import pytest

from ebl.transliteration.domain.atf import AtfSyntaxError, validate_atf, \
    to_sub_index_string


def test_valid_atf():
    validate_atf('1. foo')


def test_invalid_atf():
    with pytest.raises(AtfSyntaxError,
                       match='Line 1 is invalid.') as excinfo:
        validate_atf('$ this is not valid')

    assert excinfo.value.line_number == 1


@pytest.mark.parametrize('number,expected', [
    (None, ''),
    (1, '₁'),
    (2, '₂'),
    (3, '₃'),
    (4, '₄'),
    (5, '₅'),
    (6, '₆'),
    (7, '₇'),
    (8, '₈'),
    (9, '₉'),
    (0, '₀'),
    (124, '₁₂₄')
])
def test_to_sub_index_string(number, expected):
    assert to_sub_index_string(number) == expected
