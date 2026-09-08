from ebl.transliteration.domain.signs_transformer import name_arguments

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken, Variant
from ebl.transliteration.domain.word_tokens import Word

TEXT_MERGE_CASES_1 = [
    (
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [
                                Reading.of_name("ha"),
                                Joiner.hyphen(),
                                Reading.of_name("am"),
                            ]
                        )
                    ],
                ),
                ControlLine("#", " comment"),
            ]
        ),
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [
                                Reading.of_name("ha"),
                                Joiner.hyphen(),
                                Reading.of_name("am"),
                            ]
                        )
                    ],
                ),
                ControlLine("#", " comment"),
            ]
        ),
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [
                                Reading.of_name("ha"),
                                Joiner.hyphen(),
                                Reading.of_name("am"),
                            ]
                        )
                    ],
                ),
                ControlLine("#", " comment"),
            ]
        ),
    ),
    (
        Text.of_iterable([EmptyLine()]),
        Text.of_iterable([RulingDollarLine(atf.Ruling.SINGLE)]),
        Text.of_iterable([RulingDollarLine(atf.Ruling.SINGLE)]),
    ),
    (
        Text.of_iterable(
            [
                RulingDollarLine(atf.Ruling.DOUBLE),
                RulingDollarLine(atf.Ruling.SINGLE),
                EmptyLine(),
            ]
        ),
        Text.of_iterable([RulingDollarLine(atf.Ruling.DOUBLE), EmptyLine()]),
        Text.of_iterable([RulingDollarLine(atf.Ruling.DOUBLE), EmptyLine()]),
    ),
    (
        Text.of_iterable([EmptyLine(), RulingDollarLine(atf.Ruling.DOUBLE)]),
        Text.of_iterable(
            [
                EmptyLine(),
                RulingDollarLine(atf.Ruling.SINGLE),
                RulingDollarLine(atf.Ruling.DOUBLE),
            ]
        ),
        Text.of_iterable(
            [
                EmptyLine(),
                RulingDollarLine(atf.Ruling.SINGLE),
                RulingDollarLine(atf.Ruling.DOUBLE),
            ]
        ),
    ),
    (
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [Reading.of_name("nu")], unique_lemma=(WordId("nu I"),)
                        ),
                        Word.of(
                            [Reading.of_name("nu")], unique_lemma=(WordId("nu I"),)
                        ),
                    ],
                )
            ]
        ),
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of([Reading.of_name("mu")]),
                        Word.of([Reading.of_name("nu")]),
                    ],
                )
            ]
        ),
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of([Reading.of_name("mu")]),
                        Word.of(
                            [Reading.of_name("nu")], unique_lemma=(WordId("nu I"),)
                        ),
                    ],
                )
            ]
        ),
    ),
    (
        Text.of_iterable([ControlLine("$", " double ruling")]),
        Text.of_iterable([RulingDollarLine(atf.Ruling.DOUBLE)]),
        Text.of_iterable([RulingDollarLine(atf.Ruling.DOUBLE)]),
    ),
    (
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [
                                Variant.of(
                                    Reading.of([ValueToken.of("k[ur")]),
                                    Reading.of([ValueToken.of("r[a")]),
                                )
                            ]
                        ),
                        BrokenAway.close(),
                    ],
                )
            ]
        ),
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [
                                Variant.of(
                                    Reading.of_arguments(
                                        name_arguments(
                                            [
                                                ValueToken.of("k"),
                                                BrokenAway.open(),
                                                ValueToken.of("ur"),
                                            ]
                                        )
                                    ),
                                    Reading.of_arguments(
                                        name_arguments(
                                            [
                                                ValueToken.of("r"),
                                                BrokenAway.open(),
                                                ValueToken.of("a"),
                                            ]
                                        )
                                    ),
                                )
                            ]
                        ),
                        BrokenAway.close(),
                    ],
                )
            ]
        ),
        Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    [
                        Word.of(
                            [
                                Variant.of(
                                    Reading.of_arguments(
                                        name_arguments(
                                            [
                                                ValueToken.of("k"),
                                                BrokenAway.open(),
                                                ValueToken.of("ur"),
                                            ]
                                        )
                                    ),
                                    Reading.of_arguments(
                                        name_arguments(
                                            [
                                                ValueToken.of("r"),
                                                BrokenAway.open(),
                                                ValueToken.of("a"),
                                            ]
                                        )
                                    ),
                                )
                            ]
                        ),
                        BrokenAway.close(),
                    ],
                )
            ]
        ),
    ),
]
