from typing import Tuple

import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
    TextLine,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import (
    Joiner,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import Word

LINES: Tuple[Line, ...] = (
    TextLine.of_iterable(
        LineNumberLabel.from_atf("1."),
        [
            Word(
                "ha-am",
                parts=[Reading.of_name("ha"), Joiner.hyphen(), Reading.of_name("am"),],
            )
        ],
    ),
    ControlLine.of_single("$", ValueToken(" single ruling")),
)
PARSER_VERSION = "1.0.0"
TEXT: Text = Text(LINES, PARSER_VERSION)


def test_of_iterable():
    assert Text.of_iterable(LINES) == Text(LINES, atf.ATF_PARSER_VERSION)


def test_lines():
    assert TEXT.lines == LINES


def test_version():
    assert TEXT.parser_version == PARSER_VERSION


def test_set_version():
    new_version = "2.0.0"
    assert TEXT.set_parser_version(new_version).parser_version == new_version


def test_lemmatization():
    assert TEXT.lemmatization == Lemmatization(
        (
            (LemmatizationToken("ha-am", tuple()),),
            (LemmatizationToken(" single ruling"),),
        )
    )


def test_atf():
    assert TEXT.atf == atf.Atf("1. ha-am\n" "$ single ruling")


def test_update_lemmatization():
    tokens = TEXT.lemmatization.to_list()
    tokens[0][0]["uniqueLemma"] = ["nu I"]
    lemmatization = Lemmatization.from_list(tokens)

    expected = Text(
        (
            TextLine(
                "1.",
                (
                    Word(
                        "ha-am",
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            Reading.of_name("ha"),
                            Joiner.hyphen(),
                            Reading.of_name("am"),
                        ],
                    ),
                ),
            ),
            ControlLine("$", (ValueToken(" single ruling"),)),
        ),
        TEXT.parser_version,
    )

    assert TEXT.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    lemmatization = Lemmatization(((LemmatizationToken("mu", tuple()),),))
    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lines():
    tokens = [*TEXT.lemmatization.to_list(), []]
    lemmatization = Lemmatization.from_list(tokens)

    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (Text.of_iterable(LINES), Text.of_iterable(LINES), Text.of_iterable(LINES),),
        (
            Text.of_iterable([EmptyLine()]),
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken(" single ruling"))]
            ),
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken(" single ruling"))]
            ),
        ),
        (
            Text.of_iterable(
                [
                    ControlLine.of_single("$", ValueToken(" double ruling")),
                    ControlLine.of_single("$", ValueToken(" single ruling")),
                    EmptyLine(),
                ]
            ),
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken(" double ruling")), EmptyLine(),]
            ),
            Text.of_iterable(
                [ControlLine.of_single("$", ValueToken(" double ruling")), EmptyLine(),]
            ),
        ),
        (
            Text.of_iterable(
                [EmptyLine(), ControlLine.of_single("$", ValueToken(" double ruling")),]
            ),
            Text.of_iterable(
                [
                    EmptyLine(),
                    ControlLine.of_single("$", ValueToken(" single ruling")),
                    ControlLine.of_single("$", ValueToken(" double ruling")),
                ]
            ),
            Text.of_iterable(
                [
                    EmptyLine(),
                    ControlLine.of_single("$", ValueToken(" single ruling")),
                    ControlLine.of_single("$", ValueToken(" double ruling")),
                ]
            ),
        ),
        (
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumberLabel.from_atf("1."),
                        [
                            Word("nu", unique_lemma=(WordId("nu I"),), parts=[]),
                            Word("nu", unique_lemma=(WordId("nu I"),), parts=[]),
                        ],
                    )
                ]
            ),
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumberLabel.from_atf("1."),
                        [
                            Word("mu", parts=[Reading.of_name("mu")]),
                            Word("nu", parts=[Reading.of_name("nu")]),
                        ],
                    )
                ]
            ),
            Text.of_iterable(
                [
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
                    )
                ]
            ),
        ),
        (
            Text.of_iterable(
                [
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
                    )
                ]
            ),
            Text.of_iterable(
                [
                    TextLine.of_iterable(
                        LineNumberLabel.from_atf("1."),
                        [
                            Word("mu", parts=[Reading.of_name("mu")]),
                            Word("nu", parts=[Reading.of_name("nu")]),
                        ],
                    )
                ]
            ),
            Text.of_iterable(
                [
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
                    )
                ]
            ),
        ),
    ],
)
def test_merge(old: Text, new: Text, expected: Text) -> None:
    new_version = f"{old.parser_version}-test"
    assert old.merge(
        new.set_parser_version(new_version)
    ) == expected.set_parser_version(new_version)
