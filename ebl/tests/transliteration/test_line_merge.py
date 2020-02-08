import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    DocumentOrientedGloss,
    PerhapsBrokenAway,
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
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
            ControlLine.of_single("$", ValueToken(" single ruling")),
            ControlLine.of_single("$", ValueToken(" single ruling")),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("2."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("2."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [Word("bu", parts=[])]
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    )
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("bu", parts=[Reading.of_name("bu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    )
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    )
                ],
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
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    )
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("mu", parts=[Reading.of_name("mu")])],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [Word("mu", parts=[Reading.of_name("mu")])],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                    Word(
                        "mu",
                        unique_lemma=(WordId("mu I"),),
                        parts=[Reading.of_name("mu")],
                    ),
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("bu", parts=[Reading.of_name("bu")]),
                    Word("bu", parts=[Reading.of_name("bu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("bu", parts=[Reading.of_name("bu")]),
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word("bu", parts=[Reading.of_name("bu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word(
                        "bu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("bu")],
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(LineNumberLabel.from_atf("1."), [ValueToken("{("),]),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [DocumentOrientedGloss.open(),]
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."), [DocumentOrientedGloss.open(),]
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
                            PerhapsBrokenAway.open(),
                            Reading.of_name(
                                "ku", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                            PerhapsBrokenAway.close(),
                        ],
                    ),
                    Word(
                        "[bu]",
                        unique_lemma=(WordId("bu I"),),
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("bu"),
                            BrokenAway.close(),
                        ],
                    ),
                    Word(
                        "ku-[nu#?]",
                        unique_lemma=(WordId("kunu I"),),
                        alignment=4,
                        parts=[
                            Reading.of_name("ku"),
                            Joiner.hyphen(),
                            BrokenAway.open(),
                            Reading.of_name(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                            BrokenAway.close(),
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
                            PerhapsBrokenAway.open(),
                            Reading.of_name(
                                "ku", flags=[atf.Flag.UNCERTAIN, atf.Flag.DAMAGE],
                            ),
                            PerhapsBrokenAway.close(),
                        ],
                    ),
                    Word(
                        "[bu]",
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("bu"),
                            BrokenAway.close(),
                        ],
                    ),
                    Word(
                        "[(ku)-nu#?",
                        parts=[
                            BrokenAway.open(),
                            PerhapsBrokenAway.open(),
                            Reading.of_name("ku"),
                            PerhapsBrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                        ],
                    ),
                    BrokenAway.close(),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "(ku?#)",
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            PerhapsBrokenAway.open(),
                            Reading.of_name(
                                "ku", flags=[atf.Flag.UNCERTAIN, atf.Flag.DAMAGE],
                            ),
                            PerhapsBrokenAway.close(),
                        ],
                    ),
                    Word(
                        "[bu]",
                        unique_lemma=(WordId("bu I"),),
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("bu"),
                            BrokenAway.close(),
                        ],
                    ),
                    Word(
                        "[(ku)-nu#?",
                        unique_lemma=(WordId("kunu I"),),
                        alignment=4,
                        parts=[
                            BrokenAway.open(),
                            PerhapsBrokenAway.open(),
                            Reading.of_name("ku"),
                            PerhapsBrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
                            ),
                        ],
                    ),
                    BrokenAway.close(),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "nu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("nu")],
                    ),
                    Word(
                        "nu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("nu")],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word("nu", parts=[Reading.of_name("nu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word(
                        "nu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("nu")],
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
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word("nu", parts=[Reading.of_name("nu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word(
                        "nu",
                        unique_lemma=(WordId("nu I"),),
                        parts=[Reading.of_name("nu")],
                    ),
                ],
            ),
        ),
    ],
)
def test_merge(old: Line, new: Line, expected: Line):
    assert old.merge(new) == expected
