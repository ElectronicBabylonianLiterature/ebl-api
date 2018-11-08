import pytest
from ebl.fragmentarium.atf import validate_atf, AtfSyntaxError


def test_valid_atf():
    validate_atf('1. foo')


def test_invalid_atf():
    with pytest.raises(AtfSyntaxError,
                       message="Invalid token 'is' at line 1.") as excinfo:
        validate_atf('$ this is not valid')

    assert excinfo.value.lineno == 1
    assert excinfo.value.text == 'is'
