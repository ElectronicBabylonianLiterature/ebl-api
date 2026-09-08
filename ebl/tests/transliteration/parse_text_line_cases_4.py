from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    Variant,
)
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    LoneDeterminative,
    Word,
)

PARSE_TEXT_LINE_CASES_4 = [
    (
        "1. {bu}-nu {bu-bu}-nu\n2. {bu-bu}",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            Determinative.of([Reading.of_name("bu")]),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                        ]
                    ),
                    Word.of(
                        parts=[
                            Determinative.of(
                                [
                                    Reading.of_name("bu"),
                                    Joiner.hyphen(),
                                    Reading.of_name("bu"),
                                ]
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                        ]
                    ),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2),
                (
                    LoneDeterminative.of_value(
                        [
                            Determinative.of(
                                [
                                    Reading.of_name("bu"),
                                    Joiner.hyphen(),
                                    Reading.of_name("bu"),
                                ]
                            )
                        ],
                        ErasureState.NONE,
                    ),
                ),
            ),
        ],
    ),
    (
        "1. KIMIN {u₂#}[...] {u₂#} [...]",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of([Logogram.of_name("KIMIN")]),
                    Word.of(
                        parts=[
                            Determinative.of(
                                [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                            ),
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                    LoneDeterminative.of_value(
                        [
                            Determinative.of(
                                [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                            )
                        ],
                        ErasureState.NONE,
                    ),
                    Word.of(
                        (
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        )
                    ),
                ),
            )
        ],
    ),
    (
        "1. šu gid₂\n2. [U₄].14.KAM₂ U₄.15.KAM₂",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of([Reading.of_name("šu")]),
                    Word.of([Reading.of_name("gid", 2)]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            Logogram.of_name("U", 4),
                            BrokenAway.close(),
                            Joiner.dot(),
                            Number.of_name("14"),
                            Joiner.dot(),
                            Logogram.of_name("KAM", 2),
                        ]
                    ),
                    Word.of(
                        parts=[
                            Logogram.of_name("U", 4),
                            Joiner.dot(),
                            Number.of_name("15"),
                            Joiner.dot(),
                            Logogram.of_name("KAM", 2),
                        ]
                    ),
                ),
            ),
        ],
    ),
    (
        "1. {(he-pi₂ eš-šu₂)}\n2. {(NU SUR)}",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    DocumentOrientedGloss.open(),
                    Word.of(
                        parts=[
                            Reading.of_name("he"),
                            Joiner.hyphen(),
                            Reading.of_name("pi", 2),
                        ]
                    ),
                    Word.of(
                        parts=[
                            Reading.of_name("eš"),
                            Joiner.hyphen(),
                            Reading.of_name("šu", 2),
                        ]
                    ),
                    DocumentOrientedGloss.close(),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2),
                (
                    DocumentOrientedGloss.open(),
                    Word.of([Logogram.of_name("NU")]),
                    Word.of([Logogram.of_name("SUR")]),
                    DocumentOrientedGloss.close(),
                ),
            ),
        ],
    ),
    (
        "1.  sal/: šim ",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Variant.of(Reading.of_name("sal"), Divider.of(":")),
                    Word.of([Reading.of_name("šim")]),
                ),
            )
        ],
    ),
]
