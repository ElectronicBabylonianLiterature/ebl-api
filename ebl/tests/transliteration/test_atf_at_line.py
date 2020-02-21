import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.at_line import AtLine


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [("@fragment a", [AtLine(atf.Surface.REVERSE, atf.Status.COLLATION)]),],
)
def test_parse_atf_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines
