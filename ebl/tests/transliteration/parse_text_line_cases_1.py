from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Column,
    Joiner,
    LineBreak,
    Tabulation,
    UnknownNumberOfSigns,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import (
    Word,
)

PARSE_TEXT_LINE_CASES_1 = [
    (
        "1′. ...",
        [
            TextLine.of_iterable(
                LineNumber(1, True), (Word.of((UnknownNumberOfSigns.of(),)),)
            )
        ],
    ),
    (
        "1’. ...",
        [
            TextLine.of_iterable(
                LineNumber(1, True), (Word.of((UnknownNumberOfSigns.of(),)),)
            )
        ],
    ),
    (
        "D+113'a. ...",
        [
            TextLine.of_iterable(
                LineNumber(113, True, "D", "a"),
                (Word.of((UnknownNumberOfSigns.of(),)),),
            )
        ],
    ),
    (
        "z+113'a-9b. ...",
        [
            TextLine.of_iterable(
                LineNumberRange(
                    LineNumber(113, True, "z", "a"), LineNumber(9, False, None, "b")
                ),
                (Word.of((UnknownNumberOfSigns.of(),)),),
            )
        ],
    ),
    ("1. ($___$)", [TextLine.of_iterable(LineNumber(1), (Tabulation.of(),))]),
    (
        "1. ... [...] [(...)]",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of((UnknownNumberOfSigns.of(),)),
                    Word.of(
                        (
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        )
                    ),
                    Word.of(
                        (
                            BrokenAway.open(),
                            PerhapsBrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            PerhapsBrokenAway.close(),
                            BrokenAway.close(),
                        )
                    ),
                ),
            )
        ],
    ),
    (
        "1. [(x x x)]",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            PerhapsBrokenAway.open(),
                            UnclearSign.of(),
                        ]
                    ),
                    Word.of([UnclearSign.of()]),
                    Word.of(
                        parts=[
                            UnclearSign.of(),
                            PerhapsBrokenAway.close(),
                            BrokenAway.close(),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "1. <en-da-ab-su₈ ... >",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            AccidentalOmission.open(),
                            Reading.of_name("en"),
                            Joiner.hyphen(),
                            Reading.of_name("da"),
                            Joiner.hyphen(),
                            Reading.of_name("ab"),
                            Joiner.hyphen(),
                            Reading.of_name("su", 8),
                        ]
                    ),
                    Word.of((UnknownNumberOfSigns.of(),)),
                    AccidentalOmission.close(),
                ),
            )
        ],
    ),
    (
        "1. <<en ...>>",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of([Removal.open(), Reading.of_name("en")]),
                    Word.of((UnknownNumberOfSigns.of(), Removal.close())),
                ),
            )
        ],
    ),
    (
        "1. & &12",
        [TextLine.of_iterable(LineNumber(1), (Column.of(), Column.of(12)))],
    ),
    (
        "1. | : :' :\" :. :: ; /",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    LineBreak.of(),
                    Divider.of(":"),
                    Divider.of(":'"),
                    Divider.of(':"'),
                    Divider.of(":."),
                    Divider.of("::"),
                    Divider.of(";"),
                    Divider.of("/"),
                ),
            )
        ],
    ),
    (
        "1. ;/: :'/sal //: ://",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Variant.of(Divider.of(";"), Divider.of(":")),
                    Variant.of(Divider.of(":'"), Reading.of_name("sal")),
                    Variant.of(Divider.of("/"), Divider.of(":")),
                    Variant.of(Divider.of(":"), Divider.of("/")),
                ),
            )
        ],
    ),
    (
        "1. me-e+li  me.e:li :\n2. ku",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        [
                            Reading.of_name("me"),
                            Joiner.hyphen(),
                            Reading.of_name("e"),
                            Joiner.plus(),
                            Reading.of_name("li"),
                        ]
                    ),
                    Word.of(
                        [
                            Reading.of_name("me"),
                            Joiner.dot(),
                            Reading.of_name("e"),
                            Joiner.colon(),
                            Reading.of_name("li"),
                        ]
                    ),
                    Divider.of(":"),
                ),
            ),
            TextLine.of_iterable(LineNumber(2), (Word.of([Reading.of_name("ku")]),)),
        ],
    ),
]
