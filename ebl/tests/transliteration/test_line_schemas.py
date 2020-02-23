import pytest

from ebl.transliteration.application.line_schemas import (
    dump_line,
    load_line,
)
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import AtLine, Seal
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
)
from ebl.transliteration.domain.dollar_line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
    (
        AtLine(Seal(1), None, ""),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("TODO")]),
            "type": "AtLine",
            "structural_tag_type": "Seal",
            "structural_tag": 1,
            "status": None,
            "text": "",
        },
    ),
    (
        AtLine(atf.Surface.SURFACE, atf.Status.COLLATION, ""),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("TODO")]),
            "type": "AtLine",
            "structural_tag_type": "Surface",
            "structural_tag": "SURFACE",
            "status": "COLLATION",
            "text": "",
        },
    ),
    (
        AtLine(atf.Object.OBJECT, atf.Status.COLLATION, "stone Wig"),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("TODO")]),
            "type": "AtLine",
            "structural_tag_type": "Object",
            "structural_tag": "OBJECT",
            "status": "COLLATION",
            "text": "stone Wig",
        },
    ),
    (
        StateDollarLine(
            atf.Qualification.AT_LEAST,
            (1, 2),
            ScopeContainer(atf.Surface.SURFACE, "thing"),
            atf.State.BLANK,
            atf.Status.UNCERTAIN,
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken(" at least 1-2 surface thing blank ?")]),
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": (1, 2),
            "scope": {"type": "Surface", "content": "SURFACE", "text": "thing"},
            "state": "BLANK",
            "status": "UNCERTAIN",
        },
    ),
    (
        StateDollarLine(
            atf.Qualification.AT_LEAST,
            1,
            ScopeContainer(atf.Surface.OBVERSE),
            atf.State.BLANK,
            atf.Status.UNCERTAIN,
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken(" at least 1 obverse blank ?")]),
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": 1,
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "BLANK",
            "status": "UNCERTAIN",
        },
    ),
    (
        StateDollarLine(
            None,
            atf.Extent.BEGINNING_OF,
            ScopeContainer(atf.Surface.OBVERSE),
            None,
            None,
        ),
        {
            "prefix": "$",
            "content": dump_tokens([ValueToken(" beginning of obverse")]),
            "type": "StateDollarLine",
            "qualification": None,
            "extent": "BEGINNING_OF",
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
    (
        LooseDollarLine("end of side"),
        {
            "type": "LooseDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken(" (end of side)")]),
            "text": "end of side",
        },
    ),
    (
        ImageDollarLine("1", "a", "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken(" (image 1a = great)")]),
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
            "content": dump_tokens([ValueToken(" (image 1 = great)")]),
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
            "content": dump_tokens([ValueToken(" double ruling")]),
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
