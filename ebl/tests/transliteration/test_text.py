from typing import Sequence

import pytest  # pyre-ignore[21]

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import ColumnAtLine, SurfaceAtLine, ObjectAtLine
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.transliteration.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Label, Text
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.word_tokens import Word


LINES: Sequence[Line] = (
    TextLine(
        LineNumber(1),
        (Word.of([Reading.of_name("ha"), Joiner.hyphen(), Reading.of_name("am")]),),
    ),
    RulingDollarLine(atf.Ruling.SINGLE),
)
PARSER_VERSION = "1.0.0"
TEXT: Text = Text(LINES, PARSER_VERSION)


def test_of_iterable() -> None:
    assert Text.of_iterable(LINES) == Text(LINES, atf.ATF_PARSER_VERSION)


def test_lines() -> None:
    assert TEXT.lines == LINES


def test_text_lines() -> None:
    assert TEXT.text_lines == LINES[:1]


def test_number_of_lines() -> None:
    assert TEXT.number_of_lines == 1


def test_version() -> None:
    assert TEXT.parser_version == PARSER_VERSION


def test_set_version() -> None:
    new_version = "2.0.0"
    assert TEXT.set_parser_version(new_version).parser_version == new_version


def test_lemmatization() -> None:
    assert TEXT.lemmatization == Lemmatization(
        (
            (LemmatizationToken("ha-am", tuple()),),
            (LemmatizationToken(" single ruling"),),
        )
    )


def test_atf() -> None:
    assert TEXT.atf == atf.Atf("1. ha-am\n" "$ single ruling")


def test_update_lemmatization() -> None:
    tokens = [list(line) for line in TEXT.lemmatization.tokens]
    tokens[0][0] = LemmatizationToken(tokens[0][0].value, (WordId("nu I"),))
    lemmatization = Lemmatization(tokens)

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
            RulingDollarLine(atf.Ruling.SINGLE),
        ),
        TEXT.parser_version,
    )

    assert TEXT.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible() -> None:
    lemmatization = Lemmatization(((LemmatizationToken("mu", tuple()),),))
    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lines() -> None:
    lemmatization = Lemmatization((*TEXT.lemmatization.tokens, tuple()))

    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_labels() -> None:
    text = Text.of_iterable(
        [
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            ColumnAtLine(ColumnLabel.from_int(1)),
            SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "Stone wig")),
            ObjectAtLine(ObjectLabel([], atf.Object.OBJECT, "Stone wig")),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
        ]
    )
    assert text.labels == [
        Label(None, None, None, LineNumber(1)),
        Label(
            ColumnLabel.from_int(1),
            SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
            ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
            LineNumber(2),
        ),
    ]
