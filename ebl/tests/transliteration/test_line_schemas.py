import pytest  # pyre-ignore

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.corpus.domain.chapter import Stage
from ebl.corpus.domain.text import TextId
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    CompositeAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    HeadingAtLine,
    ObjectAtLine,
    SealAtLine,
    SurfaceAtLine,
)
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    SealDollarLine,
    StateDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.note_line import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    NoteLine,
    StringPart,
)
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    CorpusType,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ErasureState, ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
    (
        CompositeAtLine(atf.Composite.MILESTONE, "o"),
        {
            "prefix": "@",
            "content": [
                OneOfTokenSchema().dump(ValueToken.of("m=locator o"))  # pyre-ignore[16]
            ],
            "type": "CompositeAtLine",
            "composite": "MILESTONE",
            "text": "o",
            "number": None,
            "displayValue": "m=locator o",
        },
    ),
    (
        CompositeAtLine(atf.Composite.MILESTONE, "o", 1),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("m=locator o 1"))],
            "type": "CompositeAtLine",
            "composite": "MILESTONE",
            "text": "o",
            "number": 1,
            "displayValue": "m=locator o 1",
        },
    ),
    (
        CompositeAtLine(atf.Composite.COMPOSITE, ""),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("composite"))],
            "type": "CompositeAtLine",
            "composite": "COMPOSITE",
            "text": "",
            "number": None,
            "displayValue": "composite",
        },
    ),
    (
        CompositeAtLine(atf.Composite.END, "part"),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("end part"))],
            "type": "CompositeAtLine",
            "composite": "END",
            "text": "part",
            "number": None,
            "displayValue": "end part",
        },
    ),
    (
        CompositeAtLine(atf.Composite.DIV, "part", 5),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("div part 5"))],
            "type": "CompositeAtLine",
            "composite": "DIV",
            "text": "part",
            "number": 5,
            "displayValue": "div part 5",
        },
    ),
    (
        DivisionAtLine("paragraph", 5),
        {
            "prefix": "@",
            "content": [
                OneOfTokenSchema().dump(ValueToken.of("m=division paragraph 5"))
            ],
            "type": "DivisionAtLine",
            "text": "paragraph",
            "number": 5,
            "displayValue": "m=division paragraph 5",
        },
    ),
    (
        DivisionAtLine("paragraph"),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("m=division paragraph"))],
            "type": "DivisionAtLine",
            "text": "paragraph",
            "number": None,
            "displayValue": "m=division paragraph",
        },
    ),
    (
        DiscourseAtLine(atf.Discourse.DATE),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("date"))],
            "type": "DiscourseAtLine",
            "discourse_label": "DATE",
            "displayValue": "date",
        },
    ),
    (
        ObjectAtLine(
            ObjectLabel(
                [atf.Status.CORRECTION, atf.Status.COLLATION],
                atf.Object.OBJECT,
                "stone wig",
            )
        ),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("object stone wig!*"))],
            "type": "ObjectAtLine",
            "label": {
                "status": ["CORRECTION", "COLLATION"],
                "object": "OBJECT",
                "text": "stone wig",
                "abbreviation": "stone wig",
            },
            "displayValue": "object stone wig!*",
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
            "content": [OneOfTokenSchema().dump(ValueToken.of("surface stone wig!*"))],
            "type": "SurfaceAtLine",
            "surface_label": {
                "status": ["CORRECTION", "COLLATION"],
                "surface": "SURFACE",
                "text": "stone wig",
                "abbreviation": "stone wig",
            },
            "displayValue": "surface stone wig!*",
        },
    ),
    (
        ColumnAtLine(ColumnLabel([atf.Status.CORRECTION, atf.Status.COLLATION], 1)),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("column 1!*"))],
            "type": "ColumnAtLine",
            "column_label": {
                "status": ["CORRECTION", "COLLATION"],
                "column": 1,
                "abbreviation": "i",
            },
            "displayValue": "column 1!*",
        },
    ),
    (
        SealAtLine(1),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("seal 1"))],
            "type": "SealAtLine",
            "number": 1,
            "displayValue": "seal 1",
        },
    ),
    (
        HeadingAtLine(1),
        {
            "prefix": "@",
            "content": [OneOfTokenSchema().dump(ValueToken.of("h1"))],
            "type": "HeadingAtLine",
            "number": 1,
            "displayValue": "h1",
        },
    ),
    (
        StateDollarLine(
            atf.Qualification.AT_LEAST,
            atf.Extent.BEGINNING_OF,
            ScopeContainer(atf.Surface.OBVERSE),
            atf.State.BLANK,
            atf.DollarStatus.UNCERTAIN,
        ),
        {
            "prefix": "$",
            "content": [
                OneOfTokenSchema().dump(
                    ValueToken.of(" at least beginning of obverse blank ?")
                )
            ],
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": "BEGINNING_OF",
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "BLANK",
            "status": "UNCERTAIN",
            "displayValue": "at least beginning of obverse blank ?",
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
            "content": [
                OneOfTokenSchema().dump(
                    ValueToken.of(" at least 1-2 surface thing blank ?")
                )
            ],
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": [1, 2],
            "scope": {"type": "Surface", "content": "SURFACE", "text": "thing"},
            "state": "BLANK",
            "status": "UNCERTAIN",
            "displayValue": "at least 1-2 surface thing blank ?",
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
            "content": [
                OneOfTokenSchema().dump(ValueToken.of(" at least 1 obverse blank ?"))
            ],
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": 1,
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "BLANK",
            "status": "UNCERTAIN",
            "displayValue": "at least 1 obverse blank ?",
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
            "content": [
                OneOfTokenSchema().dump(ValueToken.of(" beginning of obverse"))
            ],
            "type": "StateDollarLine",
            "qualification": None,
            "extent": "BEGINNING_OF",
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": None,
            "status": None,
            "displayValue": "beginning of obverse",
        },
    ),
    (
        StateDollarLine(
            None, (2, 4), ScopeContainer(atf.Scope.LINES), atf.State.MISSING, None
        ),
        {
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" 2-4 lines missing"))],
            "type": "StateDollarLine",
            "qualification": None,
            "extent": [2, 4],
            "scope": {"type": "Scope", "content": "LINES", "text": ""},
            "state": "MISSING",
            "status": None,
            "displayValue": "2-4 lines missing",
        },
    ),
    (
        ControlLine("#", " comment"),
        {
            "type": "ControlLine",
            "prefix": "#",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" comment"))],
        },
    ),
    (
        TextLine.of_iterable(
            LineNumber(1),
            (
                DocumentOrientedGloss.open(),
                Word.of([Reading.of_name("bu")]),
                LoneDeterminative.of([Determinative.of([Reading.of_name("d")])]),
                DocumentOrientedGloss.close(),
            ),
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "lineNumber": OneOfLineNumberSchema().dump(  # pyre-ignore[16]
                LineNumber(1)
            ),
            "content": OneOfTokenSchema().dump(
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
                                        ErasureState.NONE,
                                        "bu",
                                    ),
                                )
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            )
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
                                                ErasureState.NONE,
                                                "d",
                                            ),
                                        )
                                    ).set_enclosure_type(
                                        frozenset(
                                            {EnclosureType.DOCUMENT_ORIENTED_GLOSS}
                                        )
                                    )
                                ]
                            ).set_enclosure_type(
                                frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                            )
                        ]
                    ).set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                    DocumentOrientedGloss.close().set_enclosure_type(
                        frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                    ),
                ],
                many=True,
            ),
        },
    ),
    (EmptyLine(), {"type": "EmptyLine", "prefix": "", "content": []}),
    (
        LooseDollarLine("end of side"),
        {
            "type": "LooseDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" (end of side)"))],
            "text": "end of side",
            "displayValue": "(end of side)",
        },
    ),
    (
        ImageDollarLine("1", "a", "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" (image 1a = great)"))],
            "number": "1",
            "letter": "a",
            "text": "great",
            "displayValue": "(image 1a = great)",
        },
    ),
    (
        ImageDollarLine("1", None, "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" (image 1 = great)"))],
            "number": "1",
            "letter": None,
            "text": "great",
            "displayValue": "(image 1 = great)",
        },
    ),
    (
        RulingDollarLine(atf.Ruling.DOUBLE),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" double ruling"))],
            "number": "DOUBLE",
            "status": None,
            "displayValue": "double ruling",
        },
    ),
    (
        RulingDollarLine(atf.Ruling.DOUBLE, atf.DollarStatus.COLLATED),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" double ruling *"))],
            "number": "DOUBLE",
            "status": "COLLATED",
            "displayValue": "double ruling *",
        },
    ),
    (
        SealDollarLine(1),
        {
            "type": "SealDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" seal 1"))],
            "number": 1,
            "displayValue": "seal 1",
        },
    ),
    (
        NoteLine(
            (
                StringPart("a note "),
                EmphasisPart("italic"),
                LanguagePart.of_transliteration(
                    Language.AKKADIAN, [Word.of([Reading.of_name("bu")])]
                ),
                BibliographyPart.of(BibliographyId("A"), "1-4"),
            )
        ),
        {
            "type": "NoteLine",
            "prefix": "#note: ",
            "parts": [
                {"type": "StringPart", "text": "a note "},
                {"type": "EmphasisPart", "text": "italic"},
                {
                    "type": "LanguagePart",
                    "language": Language.AKKADIAN.name,
                    "tokens": [
                        OneOfTokenSchema().dump(Word.of([Reading.of_name("bu")]))
                    ],
                },
                {
                    "type": "BibliographyPart",
                    "reference": ReferenceSchema().dump(  # pyre-ignore[16]
                        Reference(BibliographyId("A"), ReferenceType.DISCUSSION, "1-4")
                    ),
                },
            ],
            "content": OneOfTokenSchema().dump(
                [
                    ValueToken.of("a note "),
                    ValueToken.of("@i{italic}"),
                    ValueToken.of("@akk{bu}"),
                    ValueToken.of("@bib{A@1-4}"),
                ],
                many=True,
            ),
        },
    ),
    (
        ParallelFragment(
            True, MuseumNumber.of("K.1"), True, atf.Surface.OBVERSE, LineNumber(1)
        ),
        {
            "type": "ParallelFragment",
            "prefix": "//",
            "content": [OneOfTokenSchema().dump(ValueToken.of("cf. K.1 &d o 1"))],
            "displayValue": "cf. K.1 &d o 1",
            "hasCf": True,
            # pyre-ignore[16]
            "museumNumber": MuseumNumberSchema().dump(MuseumNumber.of("K.1")),
            "hasDuplicates": True,
            "surface": "OBVERSE",
            "lineNumber": OneOfLineNumberSchema().dump(LineNumber(1)),
        },
    ),
    (
        ParallelText(
            True,
            CorpusType.LITERATURE,
            TextId(1, 1),
            ChapterName(Stage.OLD_BABYLONIAN, "name"),
            LineNumber(1),
        ),
        {
            "type": "ParallelText",
            "prefix": "//",
            "content": [OneOfTokenSchema().dump(ValueToken.of("cf. L I.1 OB name 1"))],
            "displayValue": "cf. L I.1 OB name 1",
            "hasCf": True,
            "corpusType": "LITERATURE",
            "text": {"category": 1, "index": 1},
            "chapter": {"stage": "Old Babylonian", "name": "name"},
            "lineNumber": OneOfLineNumberSchema().dump(LineNumber(1)),
        },
    ),
    (
        ParallelComposition(True, "name", LineNumber(1)),
        {
            "type": "ParallelComposition",
            "prefix": "//",
            "content": [OneOfTokenSchema().dump(ValueToken.of("cf. (name 1)"))],
            "displayValue": "cf. (name 1)",
            "hasCf": True,
            "name": "name",
            "lineNumber": OneOfLineNumberSchema().dump(LineNumber(1)),
        },
    ),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    assert OneOfLineSchema().dump(line) == expected


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
            "content": [
                OneOfTokenSchema().dump(ValueToken.of(" at least 1 obverse blank ?"))
            ],
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": 1,
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "BLANK",
            "status": atf.Status.COLLATION.name,
            "displayValue": "at least 1 obverse blank ?",
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
            "content": [
                OneOfTokenSchema().dump(ValueToken.of(" at least 1 obverse blank *"))
            ],
            "type": "StateDollarLine",
            "qualification": "AT_LEAST",
            "extent": 1,
            "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
            "state": "BLANK",
            "status": atf.Status.CORRECTION.name,
            "displayValue": "at least 1 obverse blank *",
        },
    ),
    (
        RulingDollarLine(atf.Ruling.SINGLE),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": [OneOfTokenSchema().dump(ValueToken.of(" double ruling"))],
            "number": "SINGLE",
            "displayValue": "double ruling",
        },
    ),
]


@pytest.mark.parametrize("expected,data", [*LINES, *EXTRA_LINES_FOR_LOAD_LINE_TEST])
def test_load_line(expected, data):
    assert OneOfLineSchema().load(data) == expected
