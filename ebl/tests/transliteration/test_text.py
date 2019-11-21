from typing import Tuple

import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import (Lemmatization,
                                                      LemmatizationError,
                                                      LemmatizationToken)
from ebl.transliteration.domain.line import (ControlLine, EmptyLine, Line,
                                             TextLine)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import Erasure, \
    LineContinuation, \
    Side, Word, ValueToken, LanguageShift, \
    LoneDeterminative, Partial, Joiner

LINES: Tuple[Line, ...] = (
    TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('ha-am', parts=[
        ValueToken('ha'), Joiner(atf.Joiner.HYPHEN), ValueToken('am')
    ])]),
    ControlLine.of_single('$', ValueToken(' single ruling'))
)
PARSER_VERSION = '1.0.0'
TEXT: Text = Text(LINES, PARSER_VERSION)


def test_of_iterable():
    assert Text.of_iterable(LINES) == Text(LINES, atf.ATF_PARSER_VERSION)


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
    assert TEXT.atf == atf.Atf(
        '1. ha-am\n'
        '$ single ruling'
    )


def test_update_lemmatization():
    tokens = TEXT.lemmatization.to_list()
    tokens[0][0]['uniqueLemma'] = ['nu I']
    lemmatization = Lemmatization.from_list(tokens)

    expected = Text((
        TextLine('1.', (
            Word('ha-am', unique_lemma=(WordId('nu I'),), parts=[
                ValueToken('ha'), Joiner(atf.Joiner.HYPHEN), ValueToken('am')
            ]),
        )),
        ControlLine('$', (ValueToken(' single ruling'), )),
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
            ControlLine.of_single('$', ValueToken(' single ruling'))
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', ValueToken(' single ruling'))
        ])
    ), (
        Text.of_iterable([
            ControlLine.of_single('$', ValueToken(' double ruling')),
            ControlLine.of_single('$', ValueToken(' single ruling')),
            EmptyLine()
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', ValueToken(' double ruling')),
            EmptyLine()
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', ValueToken(' double ruling')),
            EmptyLine()
        ]),
    ), (
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', ValueToken(' double ruling')),
        ]),
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', ValueToken(' single ruling')),
            ControlLine.of_single('$', ValueToken(' double ruling')),
        ]),
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', ValueToken(' single ruling')),
            ControlLine.of_single('$', ValueToken(' double ruling')),
        ]),
    ), (
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('nu', unique_lemma=(WordId('nu I'),), parts=[]),
                Word('nu', unique_lemma=(WordId('nu I'),), parts=[])
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu', parts=[ValueToken('mu')]),
                Word('nu', parts=[ValueToken('nu')])
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu', parts=[ValueToken('mu')]),
                Word('nu', unique_lemma=(WordId('nu I'),),
                     parts=[ValueToken('nu')])
            ])
        ])
    ), (
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('nu', unique_lemma=(WordId('nu I'),),
                     parts=[ValueToken('nu')]),
                Word('nu', unique_lemma=(WordId('nu I'),),
                     parts=[ValueToken('nu')])
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu', parts=[ValueToken('mu')]),
                Word('nu', parts=[ValueToken('nu')])
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu', parts=[ValueToken('mu')]),
                Word('nu', unique_lemma=(WordId('nu I'),),
                     parts=[ValueToken('nu')])
            ])
        ])
    )
])
def test_merge(old: Text, new: Text, expected: Text) -> None:
    new_version = f'{old.parser_version}-test'
    assert old.merge(
        new.set_parser_version(new_version)
    ) == expected.set_parser_version(new_version)


@pytest.mark.parametrize('lines', [
    [EmptyLine()],
    [ControlLine.of_single('$', ValueToken(' single ruling'))],
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
