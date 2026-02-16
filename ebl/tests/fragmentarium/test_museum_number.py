from hamcrest.core import assert_that, all_of
from hamcrest.library import equal_to, greater_than, less_than
import pytest

from ebl.transliteration.domain.museum_number import MuseumNumber

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


PREFIXES = [
    "K",
    "Sm",
    "DT",
    "Rm",
    "Rm-II",
    "0",
    "1",
    "2",
    "11",
    "9999999",
    "BM",
    "HS",
    "CBS",
    "UM",
    "N",
    "A",
    "AA",
    "Z",
    "a",
    "zz",
]
NUMBERS_AND_SUFFIXES = ["0", "1", "2", "11", "9999999", "A", "AA", "BB", "Z", "a", "z"]


def test_order_equal() -> None:
    prefix = "X"
    number = "B"
    suffix = "C"
    assert_that(
        MuseumNumber(prefix, number, suffix),
        equal_to(MuseumNumber(prefix, number, suffix)),
    )


@pytest.mark.parametrize("prefix", PREFIXES)
def test_order_prefix(prefix: str) -> None:
    number = "B"
    suffix = "C"
    index = PREFIXES.index(prefix)
    larger = PREFIXES[index + 1 :]
    smaller = PREFIXES[:index]
    assert_that(
        MuseumNumber(prefix, number, suffix),
        all_of(
            *(  # pyre-ignore[60]
                *(
                    less_than(MuseumNumber(another, number, suffix))
                    for another in larger
                ),
                *(
                    greater_than(MuseumNumber(another, number, suffix))
                    for another in smaller
                ),
                equal_to(MuseumNumber(prefix, number, suffix)),
            )
        ),
    )


@pytest.mark.parametrize("number", NUMBERS_AND_SUFFIXES)
def test_order_number(number: str) -> None:
    prefix = "X"
    suffix = ""
    index = NUMBERS_AND_SUFFIXES.index(number)
    larger = NUMBERS_AND_SUFFIXES[index + 1 :]
    smaller = NUMBERS_AND_SUFFIXES[:index]
    assert_that(
        MuseumNumber(prefix, number, suffix),
        all_of(
            *(  # pyre-ignore[60]
                *(
                    less_than(MuseumNumber(prefix, another, suffix))
                    for another in larger
                ),
                *(
                    greater_than(MuseumNumber(prefix, another, suffix))
                    for another in smaller
                ),
            )
        ),
    )


@pytest.mark.parametrize("suffix", NUMBERS_AND_SUFFIXES)
def test_order_suffix(suffix: str) -> None:
    prefix = "X"
    number = "1"
    index = NUMBERS_AND_SUFFIXES.index(suffix)
    larger = NUMBERS_AND_SUFFIXES[index + 1 :]
    smaller = NUMBERS_AND_SUFFIXES[:index]
    assert_that(
        MuseumNumber(prefix, number, suffix),
        all_of(
            *(  # pyre-ignore[60]
                *(
                    less_than(MuseumNumber(prefix, number, another))
                    for another in larger
                ),
                *(
                    greater_than(MuseumNumber(prefix, number, another))
                    for another in smaller
                ),
            )
        ),
    )
