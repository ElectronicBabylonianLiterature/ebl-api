import pytest

from ebl.tests.transliteration.legacy_named_sign import (
    LEGACY_BREAK,
    LEGACY_PART,
    LEGACY_TAIL,
)
from ebl.transliteration.migrate_name_breaks_validation import (
    NonAlternatingName,
    separate_name_parts,
)


def test_separating_takes_alternating_positions() -> None:
    assert separate_name_parts([LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]) == (
        [LEGACY_PART, LEGACY_TAIL],
        [LEGACY_BREAK],
    )


def test_separating_an_unbroken_name_yields_no_breaks() -> None:
    assert separate_name_parts([LEGACY_PART]) == ([LEGACY_PART], [])


def test_two_adjacent_parts_are_refused_rather_than_mis_split() -> None:
    with pytest.raises(NonAlternatingName, match="position 1"):
        separate_name_parts([LEGACY_PART, LEGACY_TAIL])


def test_a_break_in_a_part_position_is_refused() -> None:
    with pytest.raises(NonAlternatingName, match="position 0"):
        separate_name_parts([LEGACY_BREAK, LEGACY_PART])


def test_a_name_part_that_is_not_a_mapping_is_refused() -> None:
    with pytest.raises(NonAlternatingName, match="position 0"):
        separate_name_parts(["ku"])


@pytest.mark.parametrize(
    "name_parts", [[LEGACY_PART, LEGACY_BREAK], []], ids=["trailing break", "empty"]
)
def test_a_name_that_does_not_end_with_a_part_is_refused(
    name_parts: list[dict[str, str]],
) -> None:
    with pytest.raises(NonAlternatingName, match="start and end with a ValueToken"):
        separate_name_parts(name_parts)


@pytest.mark.parametrize("name_parts", [None, "ku", 7, {"type": "ValueToken"}])
def test_name_parts_that_is_not_an_array_is_refused(name_parts: object) -> None:
    with pytest.raises(NonAlternatingName, match="to be an array"):
        separate_name_parts(name_parts)
