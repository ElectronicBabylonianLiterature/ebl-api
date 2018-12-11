import pytest
from ebl.atf import validate_atf, AtfSyntaxError


def test_valid_atf():
    validate_atf('1. foo')


def test_invalid_atf():
    with pytest.raises(AtfSyntaxError,
                       message="Line 1 is invalid.") as excinfo:
        validate_atf('$ this is not valid')

    assert excinfo.value.line_number == 1
    assert excinfo.value.text == 'is'
