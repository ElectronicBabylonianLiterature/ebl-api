import pytest

from ebl.transliteration.application.line_schemas import (
    dump_line,
    load_line,
)
from ebl.transliteration.application.line_number_schemas import dump_line_number
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    StringPart,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
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
            "content": dump_tokens(
                [ValueToken.of(" at least 1-2 surface thing blank ?")]
            ),
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
            "content": dump_tokens([ValueToken.of(" at least 1 obverse blank ?")]),
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
            "content": dump_tokens([ValueToken.of(" beginning of obverse")]),
            "type": "StateDollarLine",
            "qualification": None,
            "extent": "BEGINNING_OF",
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": None,
            "status": None,
        },
    ),
    (
        ControlLine.of_single("@", ValueToken.of("obverse")),
        {
            "type": "ControlLine",
            "prefix": "@",
            "content": dump_tokens([ValueToken.of("obverse")]),
        },
    ),
    (
        TextLine.of_iterable(
            LineNumber(1),
            (
                DocumentOrientedGloss.open(),
                Word.of([Reading.of_name("bu")]),
                LoneDeterminative.of([Determinative.of([Reading.of_name("d")]),],),
                DocumentOrientedGloss.close(),
            ),
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "lineNumber": dump_line_number(LineNumber(1)),
            "content": dump_tokens(
                [
                    DocumentOrientedGloss.open(),
                    Word.of(
                        [
                            Reading.of(
                                (
                                    ValueToken(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        ),
                                        "bu",
                                    ),
                                )
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            ),
                        ]
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    LoneDeterminative.of(
                        [
                            Determinative.of(
                                [
                                    Reading.of(
                                        (
                                            ValueToken(
                                                frozenset(
                                                    {
                                                        EnclosureType.DOCUMENT_ORIENTED_GLOSS
                                                    }
                                                ),
                                                "d",
                                            ),
                                        )
                                    ).set_enclosure_type(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        )
                                    ),
                                ]
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            ),
                        ],
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    DocumentOrientedGloss.close().set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                ]
            ),
        },
    ),
    (
        TextLine.of_legacy_iterable(
            LineNumberLabel.from_atf("1."),
            [
                DocumentOrientedGloss.open(),
                Word.of([Reading.of_name("bu")]),
                LoneDeterminative.of([Determinative.of([Reading.of_name("d")]),],),
                DocumentOrientedGloss.close(),
            ],
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "lineNumber": None,
            "content": dump_tokens(
                [
                    DocumentOrientedGloss.open(),
                    Word.of(
                        [
                            Reading.of(
                                (
                                    ValueToken(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        ),
                                        "bu",
                                    ),
                                )
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            ),
                        ]
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    LoneDeterminative.of(
                        [
                            Determinative.of(
                                [
                                    Reading.of(
                                        (
                                            ValueToken(
                                                frozenset(
                                                    {
                                                        EnclosureType.DOCUMENT_ORIENTED_GLOSS
                                                    }
                                                ),
                                                "d",
                                            ),
                                        )
                                    ).set_enclosure_type(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        )
                                    ),
                                ]
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            ),
                        ],
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    DocumentOrientedGloss.close().set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
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
            "content": dump_tokens([ValueToken.of(" (end of side)")]),
            "text": "end of side",
        },
    ),
    (
        ImageDollarLine("1", "a", "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken.of(" (image 1a = great)")]),
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
            "content": dump_tokens([ValueToken.of(" (image 1 = great)")]),
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
            "content": dump_tokens([ValueToken.of(" double ruling")]),
            "number": "DOUBLE",
            "status": None,
        },
    ),
    (
        RulingDollarLine(atf.Ruling.DOUBLE, atf.DollarStatus.COLLATED),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken.of(" double ruling *")]),
            "number": "DOUBLE",
            "status": "COLLATED",
        },
    ),
    (
        NoteLine(
            (
                StringPart("a note "),
                EmphasisPart("italic"),
                LanguagePart("Akkadian", Language.AKKADIAN),
            )
        ),
        {
            "type": "NoteLine",
            "prefix": "#note: ",
            "parts": [
                {"type": "StringPart", "text": "a note ",},
                {"type": "EmphasisPart", "text": "italic",},
                {
                    "type": "LanguagePart",
                    "text": "Akkadian",
                    "language": Language.AKKADIAN.name,
                },
            ],
            "content": dump_tokens(
                [
                    ValueToken.of("a note "),
                    ValueToken.of("@i{italic}"),
                    ValueToken.of("@akk{Akkadian}"),
                ]
            ),
        },
    ),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    assert dump_line(line) == expected


EXTRA_LINES_FOR_LOAD_LINE_TEST = [
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
            "content": dump_tokens([ValueToken.of(" at least 1 obverse blank ?")]),
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
            "content": dump_tokens([ValueToken.of(" at least 1 obverse blank *")]),
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
            "content": dump_tokens([ValueToken.of(" double ruling")]),
            "number": "SINGLE",
        },
    ),
    (
        TextLine.of_legacy_iterable(
            LineNumberLabel.from_atf("1."),
            [
                DocumentOrientedGloss.open(),
                Word.of([Reading.of_name("bu")]),
                LoneDeterminative.of([Determinative.of([Reading.of_name("d")]),],),
                DocumentOrientedGloss.close(),
            ],
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "content": dump_tokens(
                [
                    DocumentOrientedGloss.open(),
                    Word.of(
                        [
                            Reading.of(
                                (
                                    ValueToken(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        ),
                                        "bu",
                                    ),
                                )
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            ),
                        ]
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    LoneDeterminative.of(
                        [
                            Determinative.of(
                                [
                                    Reading.of(
                                        (
                                            ValueToken(
                                                frozenset(
                                                    {
                                                        (
                                                            EnclosureType.DOCUMENT_ORIENTED_GLOSS
                                                        )
                                                    }
                                                ),
                                                "d",
                                            ),
                                        )
                                    ).set_enclosure_type(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        )
                                    ),
                                ]
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            ),
                        ],
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    DocumentOrientedGloss.close().set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                ]
            ),
        },
    ),
]


@pytest.mark.parametrize(
    "expected,data", [*LINES, *EXTRA_LINES_FOR_LOAD_LINE_TEST],
)
def test_load_line(expected, data):
    assert load_line(data) == expected
