import pytest

from ebl.text.atf import AtfSyntaxError, validate_atf


def test_valid_atf():
    validate_atf('1. foo')


def test_invalid_atf():
    with pytest.raises(AtfSyntaxError,
                       match='Line 1 is invalid.') as excinfo:
        validate_atf('$ this is not valid')

    assert excinfo.value.line_number == 1
