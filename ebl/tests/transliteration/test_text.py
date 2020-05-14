from typing import Sequence

import pytest  # pyre-ignore

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import ColumnAtLine, SurfaceAtLine, ObjectAtLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.line import ControlLine, Line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word


LINES: Sequence[Line] = (
    TextLine(
        LineNumber(1),
        (Word.of([Reading.of_name("ha"), Joiner.hyphen(), Reading.of_name("am"),],),),
    ),
    ControlLine.of_single("$", ValueToken.of(" single ruling")),
)
PARSER_VERSION = "1.0.0"
TEXT: Text = Text(LINES, PARSER_VERSION)


def test_of_iterable():
    assert Text.of_iterable(LINES) == Text(LINES, atf.ATF_PARSER_VERSION)


def test_lines():
    assert TEXT.lines == LINES


def test_number_of_lines():
    assert TEXT.number_of_lines == 1


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
                LineNumber(1),
                (
                    Word.of(
                        unique_lemma=(WordId("nu I"),),
                        parts=[
                            Reading.of_name("ha"),
                            Joiner.hyphen(),
                            Reading.of_name("am"),
                        ],
                    ),
                ),
            ),
            ControlLine("$", (ValueToken.of(" single ruling"),)),
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


def test_labels() -> None:
    text = Text.of_iterable(
        [
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])],),
            ColumnAtLine(ColumnLabel.from_int(1)),
            SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "Stone wig")),
            ObjectAtLine([], atf.Object.OBJECT, "Stone wig"),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])],),
        ]
    )
    assert text.labels == [
        (None, None, None, LineNumber(1)),
        (
            ColumnLabel.from_int(1),
            SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
            (atf.Object.OBJECT, frozenset(), "Stone wig"),
            LineNumber(2),
        ),
    ]
