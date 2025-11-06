import pytest

from ebl.transliteration.domain.dollar_line import ImageDollarLine
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize(
    "line,expected_line",
    [
        ("$ (image 1a = great)", ImageDollarLine("1", "a", "great")),
        ("$(image 1a = great)", ImageDollarLine("1", "a", "great")),
        ("$ (image 1a = great )", ImageDollarLine("1", "a", "great")),
        ("$(image 1a = great )", ImageDollarLine("1", "a", "great")),
        (
            "$ (image 15 = numbered diagram of triangle)",
            ImageDollarLine("15", None, "numbered diagram of triangle"),
        ),
        (
            "$(image 15 = numbered diagram of triangle)",
            ImageDollarLine("15", None, "numbered diagram of triangle"),
        ),
        ("$ ((image 1a = great))", ImageDollarLine("1", "a", "great")),
        ("$((image 1a = great))", ImageDollarLine("1", "a", "great")),
    ],
)
def test_parse_image_dollar_line(line, expected_line):
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines
