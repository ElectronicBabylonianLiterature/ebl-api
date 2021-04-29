import pytest

from ebl.fragmentarium.domain.museum_number import MuseumNumber

PREFIX = "K"
NUMBER = "1"
SUFFIX = "a"


def test_museum_number() -> None:
    museum_number = MuseumNumber(PREFIX, NUMBER, SUFFIX)

    assert museum_number.prefix == PREFIX
    assert museum_number.number == NUMBER
    assert museum_number.suffix == SUFFIX
    assert str(museum_number) == f"{PREFIX}.{NUMBER}.{SUFFIX}"


def test_str_no_suffix() -> None:
    assert str(MuseumNumber(PREFIX, NUMBER)) == f"{PREFIX}.{NUMBER}"


def test_invalid_empty_prefix() -> None:
    with pytest.raises(ValueError):
        MuseumNumber("", NUMBER)


def test_invalid_period_in_prefix_no_suffix() -> None:
    with pytest.raises(ValueError):
        MuseumNumber("K.A", NUMBER)


def test_invalid_empty_number() -> None:
    with pytest.raises(ValueError):
        MuseumNumber(PREFIX, "")


def test_invalid_period_in_number() -> None:
    with pytest.raises(ValueError):
        MuseumNumber(PREFIX, "1.1")


def test_invalid_period_in_suffix() -> None:
    with pytest.raises(ValueError):
        MuseumNumber(PREFIX, NUMBER, "a.1")


def test_of_short_prefix() -> None:
    assert MuseumNumber.of(f"{PREFIX}.{NUMBER}.{SUFFIX}") == MuseumNumber(
        PREFIX, NUMBER, SUFFIX
    )


def test_of_short_prefix_no_suffix() -> None:
    assert MuseumNumber.of(f"{PREFIX}.{NUMBER}") == MuseumNumber(PREFIX, NUMBER)


def test_of_long_prefix() -> None:
    long_prefix = f"{PREFIX}.A.B"
    assert MuseumNumber.of(f"{long_prefix}.{NUMBER}.{SUFFIX}") == MuseumNumber(
        long_prefix, NUMBER, SUFFIX
    )


def test_of_invalid() -> None:
    with pytest.raises(ValueError):
        MuseumNumber.of("K.")
