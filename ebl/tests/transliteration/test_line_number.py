from typing import Optional

import pytest

from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange


@pytest.mark.parametrize(
    "line_number,number,has_prime,prefix,suffix,label,is_beginning",
    [
        (LineNumber(1), 1, False, None, None, "1", True),
        (LineNumber(1, False, None, "b"), 1, False, None, "b", "1b", True),
        (LineNumber(2), 2, False, None, None, "2", False),
        (LineNumber(1, True), 1, True, None, None, "1'", False),
        (LineNumber(1, False, "A"), 1, False, "A", None, "A+1", False),
        (LineNumber(20, True, "D", "a"), 20, True, "D", "a", "D+20'a", False),
    ],
)
def test_line_number(
    line_number: LineNumber,
    number: int,
    has_prime: bool,
    prefix: Optional[str],
    suffix: Optional[str],
    label: str,
    is_beginning: bool,
) -> None:
    assert line_number.number == number
    assert line_number.has_prime is has_prime
    assert line_number.prefix_modifier == prefix
    assert line_number.suffix_modifier == suffix
    assert line_number.atf == f"{label}."
    assert line_number.label == label
    assert line_number.is_beginning_of_side == is_beginning


@pytest.mark.parametrize(
    "start,end",
    [(LineNumber(1), LineNumber(20, True, "D", "a")), (LineNumber(2), LineNumber(1))],
)
def test_line_number_range(start: LineNumber, end: LineNumber) -> None:
    line_number = LineNumberRange(start, end)
    label = f"{start.label}-{end.label}"

    assert line_number.start == start
    assert line_number.end == end
    assert line_number.atf == f"{label}."
    assert line_number.label == label
    assert line_number.is_beginning_of_side == start.is_beginning_of_side


@pytest.mark.parametrize(
    "line_number, matching_number, expected",
    [
        (LineNumber(1), 1, True),
        (LineNumber(2), 1, False),
        (LineNumberRange(LineNumber(1), LineNumber(3)), 1, True),
        (LineNumberRange(LineNumber(1), LineNumber(3)), 2, True),
        (LineNumberRange(LineNumber(1), LineNumber(3)), 4, False),
    ],
)
def test_is_line_matching_number(line_number, matching_number, expected):
    assert line_number.is_matching_number(matching_number) == expected
