import pytest

from ebl.transliteration.application.line_schemas import dump_line, load_line
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    StrictDollarLine,
    ScopeContainer,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
    (
        StrictDollarLine(
            atf.Qualification("at least"),
            1,
            ScopeContainer(atf.Surface.from_atf("obverse")),
            atf.State("blank"),
            atf.Status("?"),
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken("at least 1 obverse blank ?")]),
            "type": "StrictDollarLine",
            "qualification": "at least",
            "extent": {"type": "int", "value": "1"},
            "scope_container": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "blank",
            "status": "?",
        },
    ),
    (
        StrictDollarLine(
            None,
            atf.Extent("beginning of"),
            ScopeContainer(atf.Surface.from_atf("obverse")),
            None,
            None,
        ),
        {
            "prefix": "$",
            "content": dump_tokens(
                [ValueToken("at least beginning of obverse blank ?")]
            ),
            "type": "StrictDollarLine",
            "qualification": None,
            "extent": {"type": "atf.Extent", "value": "Extent.BEGINNING_OF"},
            "scope_container": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": None,
            "status": None,
        },
    ),
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
                DocumentOrientedGloss("{("),
                Word("bu", parts=[Reading.of("bu")]),
                LoneDeterminative("{d}", parts=[Determinative([Reading.of("d")]),],),
            ],
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "content": dump_tokens(
                [
                    DocumentOrientedGloss("{("),
                    Word("bu", parts=[Reading.of("bu")]),
                    LoneDeterminative(
                        "{d}", parts=[Determinative([Reading.of("d")]),],
                    ),
                ]
            ),
        },
    ),
    (EmptyLine(), {"type": "EmptyLine", "prefix": "", "content": []}),
    (
        LooseDollarLine("end of side"),
        {
            "type": "LooseDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("(end of side)")]),
            "text": "end of side",
        },
    ),
    (
        ImageDollarLine("1", "a", "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("(image 1a = great)")]),
            "number": "1",
            "letter": "a",
            "text": "great",
        },
    ),
    (
        ImageDollarLine("1", None, "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("(image 1 = great)")]),
            "number": "1",
            "letter": None,
            "text": "great",
        },
    ),
    (
        RulingDollarLine(atf.Ruling("double")),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("double ruling")]),
            "number": atf.Ruling.DOUBLE.value,
        },
    ),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    x = dump_line(line)
    assert x == expected


@pytest.mark.parametrize("expected,data", LINES)
def test_load_line(expected, data):
    assert load_line(data) == expected
