import pytest
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
    LooseDollarLine,
    RulingDollarLine,
    ImageDollarLine,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import ValueToken


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("$ (image 1a = great)", [ImageDollarLine("1", "a", "great)")]),
        ("$ (end of side)", [LooseDollarLine("(end of side)")]),
    ],
)
def test_parse_atf_dollar_line_2(parser, line, expected_tokens):
    x = parser(line).lines
    y = Text.of_iterable(expected_tokens).lines
    assert x == y


def test_loose_dollar_line_of_single():
    token = "(end of side)"
    expected = LooseDollarLine(token)

    assert expected.prefix == "$"
    assert expected.content == (ValueToken("(end of side)"),)
    assert expected.text == "end of side"


def test_image_dollar_line_of_single():
    expected = ImageDollarLine("1", "a", "great)")

    assert expected.prefix == "$"
    assert expected.content == (ValueToken("( image 1a = great)"),)
    assert expected.number == "1"
    assert expected.letter == "a"
    assert expected.text == "great"
