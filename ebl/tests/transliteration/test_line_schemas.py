import pytest

from ebl.transliteration.application.line_schemas import dump_line, load_line
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
    (
        ControlLine.of_single("@", ValueToken("obverse")),
        {
            "type": "ControlLine",
            "prefix": "@",
            "content": dump_tokens([ValueToken("obverse")]),
        },
    ),
    (
        TextLine.of_iterable(
            LineNumberLabel.from_atf("1."),
            [
                DocumentOrientedGloss.open(),
                Word("bu", parts=[Reading.of_name("bu")]),
                LoneDeterminative(
                    "{d}", parts=[Determinative([Reading.of_name("d")]),],
                ),
            ],
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "content": dump_tokens(
                [
                    DocumentOrientedGloss.open(),
                    Word("bu", parts=[Reading.of_name("bu")]),
                    LoneDeterminative(
                        "{d}", parts=[Determinative([Reading.of_name("d")]),],
                    ),
                ]
            ),
        },
    ),
    (EmptyLine(), {"type": "EmptyLine", "prefix": "", "content": []}),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    assert dump_line(line) == expected


@pytest.mark.parametrize("expected,data", LINES)
def test_load_line(expected, data):
    assert load_line(data) == expected
