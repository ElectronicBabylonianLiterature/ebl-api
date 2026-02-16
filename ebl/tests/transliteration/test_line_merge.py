import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway, PerhapsBrokenAway
from ebl.transliteration.domain.line import ControlLine, EmptyLine, Line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, LanguageShift
from ebl.transliteration.domain.word_tokens import Word


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            EmptyLine(),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
        ),
        (
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            ControlLine("#", " comment"),
            ControlLine("#", " comment"),
        ),
        (
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
        ),
        (
            TextLine.of_iterable(LineNumber(1), [Word.of([])]),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    )
                ],
            ),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    )
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    )
                ],
            ),
            TextLine.of_iterable(LineNumber(1), [LanguageShift.of("%sux")]),
            TextLine.of_iterable(LineNumber(1), [LanguageShift.of("%sux")]),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    )
                ],
            ),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("mu")])]),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("mu")])]),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                    Word.of(
                        unique_lemma=(WordId("mu I"),), parts=[Reading.of_name("mu")]
                    ),
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [Word.of([Reading.of_name("bu")]), Word.of([Reading.of_name("bu")])],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of([Reading.of_name("bu")]),
                    Word.of([Reading.of_name("mu")]),
                    Word.of([Reading.of_name("bu")]),
                ],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                    Word.of([Reading.of_name("mu")]),
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]
                    ),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            PerhapsBrokenAway.open(),
                            Reading.of_name(
                                "ku", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN]
                            ),
                            PerhapsBrokenAway.close(),
                        ],
                    ),
                    Word.of(
                        unique_lemma=(WordId("bu I"),),
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("bu"),
                            BrokenAway.close(),
                        ],
                    ),
                    Word.of(
                        unique_lemma=(WordId("kunu I"),),
                        alignment=4,
                        parts=[
                            Reading.of_name("ku"),
                            Joiner.hyphen(),
                            BrokenAway.open(),
                            Reading.of_name(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN]
                            ),
                            BrokenAway.close(),
                        ],
                    ),
                ],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        parts=[
                            PerhapsBrokenAway.open(),
                            Reading.of_name(
                                "ku", flags=[atf.Flag.UNCERTAIN, atf.Flag.DAMAGE]
                            ),
                            PerhapsBrokenAway.close(),
                        ]
                    ),
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("bu"),
                            BrokenAway.close(),
                        ]
                    ),
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            PerhapsBrokenAway.open(),
                            Reading.of_name("ku"),
                            PerhapsBrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN]
                            ),
                        ]
                    ),
                    BrokenAway.close(),
                ],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            PerhapsBrokenAway.open(),
                            Reading.of_name(
                                "ku", flags=[atf.Flag.UNCERTAIN, atf.Flag.DAMAGE]
                            ),
                            PerhapsBrokenAway.close(),
                        ],
                    ),
                    Word.of(
                        unique_lemma=(WordId("bu I"),),
                        parts=[
                            BrokenAway.open(),
                            Reading.of_name("bu"),
                            BrokenAway.close(),
                        ],
                    ),
                    Word.of(
                        unique_lemma=(WordId("kunu I"),),
                        alignment=4,
                        parts=[
                            BrokenAway.open(),
                            PerhapsBrokenAway.open(),
                            Reading.of_name("ku"),
                            PerhapsBrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name(
                                "nu", flags=[atf.Flag.DAMAGE, atf.Flag.UNCERTAIN]
                            ),
                        ],
                    ),
                    BrokenAway.close(),
                ],
            ),
        ),
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of([Reading.of_name("nu")], unique_lemma=(WordId("nu I"),)),
                    Word.of([Reading.of_name("nu")], unique_lemma=(WordId("nu I"),)),
                ],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [Word.of([Reading.of_name("mu")]), Word.of([Reading.of_name("nu")])],
            ),
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of([Reading.of_name("mu")]),
                    Word.of([Reading.of_name("nu")], unique_lemma=(WordId("nu I"),)),
                ],
            ),
        ),
        (
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
        ),
    ],
)
def test_merge(old: Line, new: Line, expected: Line):
    assert old.merge(new) == expected
