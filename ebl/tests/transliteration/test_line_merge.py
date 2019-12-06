import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import ControlLine, EmptyLine, Line, TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import Joiner, LanguageShift, ValueToken
from ebl.transliteration.domain.word_tokens import Word


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            EmptyLine(),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
            ControlLine.of_single("$", ValueToken(" single ruling")),
            ControlLine.of_single("$", ValueToken(" single ruling")),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("2."), [Word("bu", parts=[Reading.of("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("2."), [Word("bu", parts=[Reading.of("bu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[])]
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],)],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[Reading.of("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],)],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],)],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [LanguageShift("%sux")]
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [LanguageShift("%sux")]
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],)],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("mu", parts=[Reading.of("mu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("mu", parts=[Reading.of("mu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                    Word(
                        "mu", unique_lemma=(WordId("mu I"),), parts=[Reading.of("mu")],
                    ),
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("bu", parts=[Reading.of("bu")]),
                    Word("bu", parts=[Reading.of("bu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("bu", parts=[Reading.of("bu")]),
                    Word("mu", parts=[Reading.of("mu")]),
                    Word("bu", parts=[Reading.of("bu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                    Word("mu", parts=[Reading.of("mu")]),
                    Word(
                        "bu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("bu")],
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(LineNumberLabel.from_atf("1."), [ValueToken("{("),]),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [DocumentOrientedGloss("{("),]
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [DocumentOrientedGloss("{("),]
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "(ku#?)",
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            ValueToken("("),
                            Reading.of(
                                "ku", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                            ValueToken(")"),
                        ],
                    ),
                    Word(
                        "[bu]",
                        unique_lemma=(WordId("bu I"),),
                        parts=[ValueToken("["), Reading.of("bu"), ValueToken("]"),],
                    ),
                    Word(
                        "ku-[nu#?]",
                        unique_lemma=(WordId("kunu I"),),
                        alignment=4,
                        parts=[
                            Reading.of("ku"),
                            Joiner.hyphen(),
                            ValueToken("["),
                            Reading.of(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                            ValueToken("]"),
                        ],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "(ku?#)",
                        parts=[
                            ValueToken("("),
                            Reading.of(
                                "ku", flags=[atf.Flag.UNCERTAIN, atf.Flag.DAMAGE],
                            ),
                            ValueToken(")"),
                        ],
                    ),
                    Word(
                        "[bu]",
                        parts=[ValueToken("["), Reading.of("bu"), ValueToken("]"),],
                    ),
                    Word(
                        "[k(u)-nu#?",
                        parts=[
                            Reading.of("k(u)"),
                            Joiner.hyphen(),
                            Reading.of(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                        ],
                    ),
                    BrokenAway("]"),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "(ku?#)",
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            ValueToken("("),
                            Reading.of(
                                "ku", flags=[atf.Flag.UNCERTAIN, atf.Flag.DAMAGE],
                            ),
                            ValueToken(")"),
                        ],
                    ),
                    Word(
                        "[bu]",
                        unique_lemma=(WordId("bu I"),),
                        parts=[ValueToken("["), Reading.of("bu"), ValueToken("]"),],
                    ),
                    Word(
                        "[k(u)-nu#?",
                        unique_lemma=(WordId("kunu I"),),
                        alignment=4,
                        parts=[
                            Reading.of("k(u)"),
                            Joiner.hyphen(),
                            Reading.of(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                        ],
                    ),
                    BrokenAway("]"),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "nu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("nu")],
                    ),
                    Word(
                        "nu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("nu")],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of("mu")]),
                    Word("nu", parts=[Reading.of("nu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of("mu")]),
                    Word(
                        "nu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("nu")],
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("nu", unique_lemma=(WordId("nu I"),), parts=[]),
                    Word("nu", unique_lemma=(WordId("nu I"),), parts=[]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of("mu")]),
                    Word("nu", parts=[Reading.of("nu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of("mu")]),
                    Word(
                        "nu", unique_lemma=(WordId("nu I"),), parts=[Reading.of("nu")],
                    ),
                ],
            ),
        ),
    ],
)
def test_merge(old: Line, new: Line, expected: Line):
    assert old.merge(new) == expected
