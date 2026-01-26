import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import EmphasisPart, LanguagePart, StringPart
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken, Variant
from ebl.transliteration.domain.word_tokens import Word


@pytest.mark.parametrize(
    "old,new,expected",
    [
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
                        LineNumber(1), [Word.of([Reading.of_name("bu")])]
                    )
                ]
            ),
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumber(1), [Word.of([Reading.of_name("bu")])]
                    )
                ]
            ),
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumber(1), [Word.of([Reading.of_name("bu")])]
                    )
                ]
            ),
        ),
        (
            Text.of_iterable([NoteLine((StringPart("this is a note "),))]),
            Text.of_iterable([NoteLine((StringPart("this is another note "),))]),
            Text.of_iterable([NoteLine((StringPart("this is another note "),))]),
        ),
        (
            Text.of_iterable([NoteLine((StringPart("this is a note "),))]),
            Text.of_iterable([NoteLine((EmphasisPart("this is a note "),))]),
            Text.of_iterable([NoteLine((EmphasisPart("this is a note "),))]),
        ),
        (
            Text.of_iterable(
                [
                    NoteLine(
                        (
                            LanguagePart.of_transliteration(
                                Language.AKKADIAN, (ValueToken.of("bu"),)
                            ),
                        )
                    )
                ]
            ),
            Text.of_iterable(
                [
                    NoteLine(
                        (
                            LanguagePart.of_transliteration(
                                Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                            ),
                        )
                    )
                ]
            ),
            Text.of_iterable(
                [
                    NoteLine(
                        (
                            LanguagePart.of_transliteration(
                                Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                            ),
                        )
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
