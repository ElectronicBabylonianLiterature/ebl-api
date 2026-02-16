from typing import Sequence

import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.transliteration_error import ExtentLabelError
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import LineLabel, Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
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
            (LemmatizationToken("ha-am", ()),),
            (LemmatizationToken(" single ruling"),),
        )
    )


def test_atf() -> None:
    assert TEXT.atf == atf.Atf("1. ha-am\n$ single ruling")


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
    lemmatization = Lemmatization(((LemmatizationToken("mu", ()),),))
    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lines() -> None:
    lemmatization = Lemmatization((*TEXT.lemmatization.tokens, ()))

    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_labels(text_with_labels) -> None:
    assert text_with_labels.labels == [
        LineLabel(None, None, None, LineNumber(1), None),
        LineLabel(
            ColumnLabel.from_int(1),
            SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
            ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
            LineNumber(2),
            None,
        ),
    ]


def test_translation_before_text() -> None:
    with pytest.raises(ExtentLabelError):
        Text.of_iterable([TranslationLine(()), *LINES])


def test_invalid_extent() -> None:
    with pytest.raises(ExtentLabelError):
        Text.of_iterable(
            [
                TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
                TranslationLine((), "en", Extent(LineNumber(3))),
                TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
            ]
        )


def test_extent_before_translation() -> None:
    with pytest.raises(ExtentLabelError):
        Text.of_iterable(
            [
                TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
                TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
                TranslationLine((), "en", Extent(LineNumber(1))),
            ]
        )


def test_exent_overlapping() -> None:
    with pytest.raises(ExtentLabelError):
        Text.of_iterable(
            [
                TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
                TranslationLine((), extent=Extent(LineNumber(2))),
                TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
                TranslationLine(()),
            ]
        )


def test_extent_overlapping_languages() -> None:
    Text.of_iterable(
        [
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            TranslationLine((), "en", Extent(LineNumber(2))),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
            TranslationLine((), "de"),
        ]
    )
