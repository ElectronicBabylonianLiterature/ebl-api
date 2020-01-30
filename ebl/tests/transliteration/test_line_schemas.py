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
            atf.Qualification.AT_LEAST,
            (1, 2),
            ScopeContainer(atf.Surface.SURFACE, "thing"),
            atf.State.BLANK,
            atf.Status.UNCERTAIN,
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken("at least 1-2 surface thing blank ?")]),
            "type": "StrictDollarLine",
            "qualification": "AT_LEAST",
            "extent": {"type": "tuple", "value": "(1, 2)"},
            "scope": {"type": "Surface", "content": "SURFACE", "text": "thing"},
            "state": "BLANK",
            "status": "UNCERTAIN",
        },
    ),
    (
        StrictDollarLine(
            atf.Qualification.AT_LEAST,
            1,
            ScopeContainer(atf.Surface.OBVERSE),
            atf.State.BLANK,
            atf.Status.UNCERTAIN,
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken("at least 1 obverse blank ?")]),
            "type": "StrictDollarLine",
            "qualification": "AT_LEAST",
            "extent": {"type": "int", "value": "1"},
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "BLANK",
            "status": "UNCERTAIN",
        },
    ),
    (
        StrictDollarLine(
            None,
            atf.Extent.BEGINNING_OF,
            ScopeContainer(atf.Surface.OBVERSE),
            None,
            None,
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken("beginning of obverse")]),
            "type": "StrictDollarLine",
            "qualification": None,
            "extent": {"type": "Extent", "value": "BEGINNING_OF"},
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
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
        RulingDollarLine(atf.Ruling.DOUBLE),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("double ruling")]),
            "number": "DOUBLE",
        },
    ),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    assert dump_line(line) == expected


@pytest.mark.parametrize("expected,data", LINES)
def test_load_line(expected, data):
    assert load_line(data) == expected
