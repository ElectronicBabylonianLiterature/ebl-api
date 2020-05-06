
import pytest  # pyre-ignore

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


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            Text.of_iterable([
                TextLine.of_iterable(
                    LineNumber(1),
                    [Word.of([
                        Reading.of_name("ha"),
                        Joiner.hyphen(),
                        Reading.of_name("am"),
                    ],)],
                ),
                ControlLine.of_single("$", ValueToken.of(" single ruling")),
            ]),
            Text.of_iterable([
                TextLine.of_iterable(
                    LineNumber(1),
                    [Word.of([
                        Reading.of_name("ha"),
                        Joiner.hyphen(),
                        Reading.of_name("am"),
                    ],)],
                ),
                ControlLine.of_single("$", ValueToken.of(" single ruling")),
            ]),
            Text.of_iterable([
                TextLine.of_iterable(
                    LineNumber(1),
                    [Word.of([
                        Reading.of_name("ha"),
                        Joiner.hyphen(),
                        Reading.of_name("am"),
                    ],)],
                ),
                ControlLine.of_single("$", ValueToken.of(" single ruling")),
            ]),
        ),
        (
            Text.of_iterable([EmptyLine()]),
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken.of(" single ruling"))]
            ),
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken.of(" single ruling"))]
            ),
        ),
        (
            Text.of_iterable(
                [
                    ControlLine.of_single("$", ValueToken.of(" double ruling")),
                    ControlLine.of_single("$", ValueToken.of(" single ruling")),
                    EmptyLine(),
                ]
            ),
            Text.of_iterable(
                [
                    ControlLine.of_single("$", ValueToken.of(" double ruling")),
                    EmptyLine(),
                ]
            ),
            Text.of_iterable(
                [
                    ControlLine.of_single("$", ValueToken.of(" double ruling")),
                    EmptyLine(),
                ]
            ),
        ),
        (
            Text.of_iterable(
                [
                    EmptyLine(),
                    ControlLine.of_single("$", ValueToken.of(" double ruling")),
                ]
            ),
            Text.of_iterable(
                [
                    EmptyLine(),
                    ControlLine.of_single("$", ValueToken.of(" single ruling")),
                    ControlLine.of_single("$", ValueToken.of(" double ruling")),
                ]
            ),
            Text.of_iterable(
                [
                    EmptyLine(),
                    ControlLine.of_single("$", ValueToken.of(" single ruling")),
                    ControlLine.of_single("$", ValueToken.of(" double ruling")),
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
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken.of(" double ruling")),]
            ),
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
                                        Reading.of(
                                            [
                                                ValueToken.of("k"),
                                                BrokenAway.open(),
                                                ValueToken.of("ur"),
                                            ]
                                        ),
                                        Reading.of(
                                            [
                                                ValueToken.of("r"),
                                                BrokenAway.open(),
                                                ValueToken.of("a"),
                                            ]
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
                                        Reading.of(
                                            [
                                                ValueToken.of("k"),
                                                BrokenAway.open(),
                                                ValueToken.of("ur"),
                                            ]
                                        ),
                                        Reading.of(
                                            [
                                                ValueToken.of("r"),
                                                BrokenAway.open(),
                                                ValueToken.of("a"),
                                            ]
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
        (
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumber(1),
                        [Word.of([Reading.of_name("bu")])],
                    )
                ]
            ),
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumber(1), [Word.of([Reading.of_name("bu")])],
                    )
                ]
            ),
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumber(1), [Word.of([Reading.of_name("bu")])],
                    )
                ]
            ),
        ),
    ],
)
def test_merge(old: Text, new: Text, expected: Text) -> None:
    new_version = f"{old.parser_version}-test"
    merged = old.merge(new.set_parser_version(new_version))
    assert merged == expected.set_parser_version(new_version)
