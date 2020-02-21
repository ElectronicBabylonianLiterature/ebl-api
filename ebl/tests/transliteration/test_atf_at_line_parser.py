import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.at_line import AtLine


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("@fragment a !", [AtLine(atf.Object.FRAGMENT, atf.Status.CORRECTION, "a")]),
        ("@reverse !", [AtLine(atf.Surface.REVERSE, atf.Status.CORRECTION)]),
        ("@surface a !", [AtLine(atf.Surface.SURFACE, atf.Status.CORRECTION, "a")]),
        ("@object what !", [AtLine(atf.Object.OBJECT, atf.Status.CORRECTION, "what")]),
    ],
)
def test_parse_atf_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines
