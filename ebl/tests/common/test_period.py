from ebl.common.domain.period import Period
import pytest


def test_mapping():
    for period in Period:
        assert Period.from_name(period.long_name) == period
        assert Period.from_abbreviation(period.abbreviation) == period


def test_invalid_name():
    with pytest.raises(ValueError, match="Unknown Period.long_name: foobar"):
        Period.from_name("foobar")


def test_invalid_abbreviation():
    with pytest.raises(ValueError, match="Unknown Period.abbreviation: foo"):
        Period.from_abbreviation("foo")
