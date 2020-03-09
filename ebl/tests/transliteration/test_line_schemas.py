import pytest

from ebl.transliteration.application.line_schemas import (
    dump_line,
    load_line,
    SealAtLine,
)
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    HeadingAtLine,
    ColumnAtLine,
    SurfaceAtLine,
    ObjectAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    CompositeAtLine,
)
from ebl.transliteration.domain.dollar_line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
    SealDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.labels import LineNumberLabel, ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
    (
        CompositeAtLine(atf.Composite.END, "part"),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("end part")]),
            "type": "CompositeAtLine",
            "composite": "END",
            "text": "part",
            "number": None,
        },
    ),
    (
        CompositeAtLine(atf.Composite.DIV, "part", 5),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("div part 5")]),
            "type": "CompositeAtLine",
            "composite": "DIV",
            "text": "part",
            "number": 5,
        },
    ),
    (
        DivisionAtLine("paragraph", 5),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("m=division paragraph 5")]),
            "type": "DivisionAtLine",
            "text": "paragraph",
            "number": 5,
        },
    ),
    (
        DivisionAtLine("paragraph"),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("m=division paragraph")]),
            "type": "DivisionAtLine",
            "text": "paragraph",
            "number": None,
        },
    ),
    (
        DiscourseAtLine(atf.Discourse.DATE),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("date")]),
            "type": "DiscourseAtLine",
            "discourse_label": "DATE",
        },
    ),
    (
        ObjectAtLine(
            [atf.Status.CORRECTION, atf.Status.COLLATION],
            atf.Object.OBJECT,
            "stone wig",
        ),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("object stone wig!*")]),
            "type": "ObjectAtLine",
            "status": ["CORRECTION", "COLLATION"],
            "object_label": "OBJECT",
            "text": "stone wig",
        },
    ),
    (
        SurfaceAtLine(
            SurfaceLabel(
                [atf.Status.CORRECTION, atf.Status.COLLATION],
                atf.Surface.SURFACE,
                "stone wig",
            )
        ),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("surface stone wig!*")]),
            "type": "SurfaceAtLine",
            "surface_label": {
                "status": ["CORRECTION", "COLLATION"],
                "surface": "SURFACE",
                "text": "stone wig",
            },
        },
    ),
    (
        ColumnAtLine(ColumnLabel([atf.Status.CORRECTION, atf.Status.COLLATION], 1)),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("column 1!*")]),
            "type": "ColumnAtLine",
            "column_label": {"status": ["CORRECTION", "COLLATION"], "column": 1},
        },
    ),
    (
        ColumnAtLine(ColumnLabel([], 1)),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("column 1")]),
            "type": "ColumnAtLine",
            "column_label": {"status": [], "column": 1},
        },
    ),
    (
        SealAtLine(1),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("seal 1")]),
            "type": "SealAtLine",
            "number": 1,
        },
    ),
    (
        HeadingAtLine(1),
        {
            "prefix": "@",
            "content": dump_tokens([ValueToken("h1")]),
            "type": "HeadingAtLine",
            "number": 1,
        },
    ),
    (
        StateDollarLine(
            atf.Qualification.AT_LEAST,
            (1, 2),
            ScopeContainer(atf.Surface.SURFACE, "thing"),
            atf.State.BLANK,
            atf.DollarStatus.UNCERTAIN,
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
            atf.DollarStatus.UNCERTAIN,
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
                Word(parts=[Reading.of_name("bu")]),
                LoneDeterminative(parts=[Determinative([Reading.of_name("d")]),],),
            ],
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "content": dump_tokens(
                [
                    DocumentOrientedGloss.open(),
                    Word(parts=[Reading.of_name("bu")]),
                    LoneDeterminative(parts=[Determinative([Reading.of_name("d")]),],),
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
            "status": None,
        },
    ),
    (
        RulingDollarLine(atf.Ruling.DOUBLE, atf.DollarStatus.COLLATED),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken(" double ruling *")]),
            "number": "DOUBLE",
            "status": "COLLATED",
        },
    ),
    (
        SealDollarLine(1),
        {
            "type": "SealDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken(" seal 1")]),
            "number": 1,
        },
    ),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    assert dump_line(line) == expected


@pytest.mark.parametrize(
    "expected,data",
    [
        *LINES,
        (
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.OBVERSE),
                atf.State.BLANK,
                atf.DollarStatus.COLLATED,
            ),
            {
                "prefix": "$",
                "content": dump_tokens([ValueToken(" at least 1 obverse blank ?")]),
                "type": "StateDollarLine",
                "qualification": "AT_LEAST",
                "extent": 1,
                "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
                "state": "BLANK",
                "status": atf.Status.COLLATION.name,
            },
        ),
        (
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.OBVERSE),
                atf.State.BLANK,
                atf.DollarStatus.EMENDED_NOT_COLLATED,
            ),
            {
                "prefix": "$",
                "content": dump_tokens([ValueToken(" at least 1 obverse blank *")]),
                "type": "StateDollarLine",
                "qualification": "AT_LEAST",
                "extent": 1,
                "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
                "state": "BLANK",
                "status": atf.Status.CORRECTION.name,
            },
        ),
        (
            RulingDollarLine(atf.Ruling.SINGLE),
            {
                "type": "RulingDollarLine",
                "prefix": "$",
                "content": dump_tokens([ValueToken(" double ruling")]),
                "number": "SINGLE",
            },
        ),
    ],
)
def test_load_line(expected, data):
    assert load_line(data) == expected
