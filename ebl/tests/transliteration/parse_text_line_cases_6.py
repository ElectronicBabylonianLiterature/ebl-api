from ebl.transliteration.domain.signs_transformer import name_arguments


from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    IntentionalOmission,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Logogram,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import (
    InWordNewline,
    Word,
)

PARSE_TEXT_LINE_CASES_6 = [
    (
        "1. [{iti}...]",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            Determinative.of([Reading.of_name("iti")]),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "2. RA{k[i}]",
        [
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            Logogram.of_name("RA"),
                            Determinative.of(
                                [
                                    Reading.of_arguments(
                                        name_arguments(
                                            (
                                                ValueToken.of("k"),
                                                BrokenAway.open(),
                                                ValueToken.of("i"),
                                            )
                                        )
                                    )
                                ]
                            ),
                            BrokenAway.close(),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "2. [in]-<(...)>",
        [
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("in"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            IntentionalOmission.open(),
                            UnknownNumberOfSigns.of(),
                            IntentionalOmission.close(),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "2. ...{d}kur ... {d}kur",
        [
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            UnknownNumberOfSigns.of(),
                            Determinative.of([Reading.of_name("d")]),
                            Reading.of_name("kur"),
                        ]
                    ),
                    Word.of((UnknownNumberOfSigns.of(),)),
                    Word.of(
                        parts=[
                            Determinative.of([Reading.of_name("d")]),
                            Reading.of_name("kur"),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "2. kur{d}... kur{d} ...",
        [
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            Reading.of_name("kur"),
                            Determinative.of([Reading.of_name("d")]),
                            UnknownNumberOfSigns.of(),
                        ]
                    ),
                    Word.of(
                        parts=[
                            Reading.of_name("kur"),
                            Determinative.of([Reading.of_name("d")]),
                        ]
                    ),
                    Word.of((UnknownNumberOfSigns.of(),)),
                ),
            )
        ],
    ),
    (
        "1. mu-un;-e₃ ;",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("un"),
                            InWordNewline.of(),
                            Joiner.hyphen(),
                            Reading.of_name("e", 3),
                        ]
                    ),
                    Divider.of(";"),
                ),
            )
        ],
    ),
    (
        "1. [... {(he-p]i₂)}",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of((BrokenAway.open(), UnknownNumberOfSigns.of())),
                    DocumentOrientedGloss.open(),
                    Word.of(
                        parts=[
                            Reading.of_name("he"),
                            Joiner.hyphen(),
                            Reading.of_arguments(
                                name_arguments(
                                    (
                                        ValueToken.of("p"),
                                        BrokenAway.close(),
                                        ValueToken.of("i"),
                                    ),
                                    2,
                                )
                            ),
                        ]
                    ),
                    DocumentOrientedGloss.close(),
                ),
            )
        ],
    ),
]
