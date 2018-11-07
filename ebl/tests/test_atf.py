import pytest
from ebl.fragmentarium.atf import validate_atf, AtfError


def test_valid_atf():
    validate_atf('1. foo')


def test_invalid_atf():
    with pytest.raises(AtfError):
        validate_atf('$ this is not valid')
