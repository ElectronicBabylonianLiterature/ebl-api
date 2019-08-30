from typing import Tuple

import pytest

from ebl.dictionary.word import WordId
from ebl.text.atf import ATF_PARSER_VERSION, Atf
from ebl.text.labels import LineNumberLabel
from ebl.text.language import Language
from ebl.text.lemmatization import (Lemmatization, LemmatizationError,
                                    LemmatizationToken)
from ebl.text.line import (ControlLine, EmptyLine, Line, TextLine)
from ebl.text.text import LanguageShift, Text
from ebl.text.token import BrokenAway, Erasure, LineContinuation, \
    PerhapsBrokenAway, Side, Token
from ebl.text.word import LoneDeterminative, Partial, Word

LINES: Tuple[Line, ...] = (
    TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('ha-am')]),
    ControlLine.of_single('$', Token(' single ruling'))
)
PARSER_VERSION = '1.0.0'
TEXT: Text = Text(LINES, PARSER_VERSION)


def test_of_iterable():
    assert Text.of_iterable(LINES) == Text(LINES, ATF_PARSER_VERSION)


def test_lines():
    assert TEXT.lines == LINES


def test_version():
    assert TEXT.parser_version == PARSER_VERSION


def test_set_version():
    new_version = '2.0.0'
    assert TEXT.set_parser_version(new_version).parser_version == new_version


def test_to_dict():
    assert TEXT.to_dict() == {
        'lines': [line.to_dict() for line in LINES],
        'parser_version': TEXT.parser_version
    }


def test_lemmatization():
    assert TEXT.lemmatization == Lemmatization((
        (LemmatizationToken('ha-am', tuple()), ),
        (LemmatizationToken(' single ruling'), ),
    ))


def test_atf():
    assert TEXT.atf == Atf(
        '1. ha-am\n'
        '$ single ruling'
    )


def test_update_lemmatization():
    tokens = TEXT.lemmatization.to_list()
    tokens[0][0]['uniqueLemma'] = ['nu I']
    lemmatization = Lemmatization.from_list(tokens)

    expected = Text((
        TextLine('1.', (
            Word('ha-am', unique_lemma=(WordId('nu I'),)),
        )),
        ControlLine('$', (Token(' single ruling'), )),
    ), TEXT.parser_version)

    assert TEXT.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    lemmatization = Lemmatization(
        ((LemmatizationToken('mu', tuple()), ), )
    )
    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lines():
    tokens = [
        *TEXT.lemmatization.to_list(),
        []
    ]
    lemmatization = Lemmatization.from_list(tokens)

    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


@pytest.mark.parametrize('old,new,expected', [
    (
        Text.of_iterable(LINES),
        Text.of_iterable(LINES),
        Text.of_iterable(LINES)
    ), (
        Text.of_iterable([EmptyLine()]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' single ruling'))
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' single ruling'))
        ])
    ), (
        Text.of_iterable([
            ControlLine.of_single('$', Token(' double ruling')),
            ControlLine.of_single('$', Token(' single ruling')),
            EmptyLine()
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' double ruling')),
            EmptyLine()
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' double ruling')),
            EmptyLine()
        ]),
    ), (
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', Token(' double ruling')),
        ]),
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', Token(' single ruling')),
            ControlLine.of_single('$', Token(' double ruling')),
        ]),
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', Token(' single ruling')),
            ControlLine.of_single('$', Token(' double ruling')),
        ]),
    ), (
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('nu', unique_lemma=(WordId('nu I'),)),
                Word('nu', unique_lemma=(WordId('nu I'),))
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu'), Word('nu')
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu'),
                Word('nu', unique_lemma=(WordId('nu I'),))
            ])
        ])
    ), (
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('[ku-(nu)]',
                     unique_lemma=(WordId('kunu I'),),
                     alignment=4),
            ]),
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                BrokenAway('['),
                Word('ku-(nu'),
                PerhapsBrokenAway(')'),
                BrokenAway(']')
            ]),
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                BrokenAway('['),
                Word('ku-(nu',
                     unique_lemma=(WordId('kunu I'),),
                     alignment=4),
                PerhapsBrokenAway(')'),
                BrokenAway(']')
            ])
        ])
    )
])
def test_merge(old: Text, new: Text, expected: Text) -> None:
    new_version = f'{old.parser_version}-test'
    assert old.merge(
        new.set_parser_version(new_version)
    ).to_dict() == expected.set_parser_version(new_version).to_dict()


@pytest.mark.parametrize('lines', [
    [EmptyLine()],
    [ControlLine.of_single('$', Token(' single ruling'))],
    [
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('nu', unique_lemma=(WordId('nu I'),)),
            Word('nu', alignment=1),
            LanguageShift('%sux'),
            LoneDeterminative(
                '{nu}',
                language=Language.SUMERIAN,
                partial=Partial(False, True)
            ),
            Erasure('°', Side.LEFT),
            Erasure('\\', Side.CENTER),
            Erasure('°', Side.RIGHT),
            LineContinuation('→')
        ])
    ]
])
def test_from_dict(lines):
    parser_version = '2.3.1'
    assert Text.from_dict({
        'lines': [line.to_dict() for line in lines],
        'parser_version': '2.3.1'
    }) == Text.of_iterable(lines).set_parser_version(parser_version)
