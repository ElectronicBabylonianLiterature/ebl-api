import pytest

from ebl.transliteration.domain.dollar_line import LooseDollarLine
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize(
    "line,expected_line",
    [
        ("$ (aa dd)", LooseDollarLine("aa dd")),
        ("$ (aa dd )", LooseDollarLine("aa dd")),
        ("$(aa dd)", LooseDollarLine("aa dd")),
        ("$(aa dd )", LooseDollarLine("aa dd")),
        ("$ ((aa dd))", LooseDollarLine("(aa dd)")),
        ("$((aa dd))", LooseDollarLine("(aa dd)")),
    ],
)
def test_parse_loose_dollar_line(line, expected_line):
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines
