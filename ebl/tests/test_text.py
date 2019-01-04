from typing import Tuple
import pytest
from ebl.text.lemmatization import (
    Lemmatization, LemmatizationToken, LemmatizationError
)
from ebl.text.atf import Atf
from ebl.text.line import Line, TextLine, ControlLine
from ebl.text.text import Text
from ebl.text.token import Word, Token


LINES: Tuple[Line, ...] = (
    TextLine('1.', (Word('ha-am'), )),
    ControlLine('$', (Token(' single ruling'), )),
)
TEXT: Text = Text(LINES)


def test_lines():
    assert TEXT.lines == LINES


def test_to_dict():
    assert TEXT.to_dict() == {
        'lines': [line.to_dict() for line in LINES]
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
        TextLine('1.', (Word('ha-am', unique_lemma=('nu I', )), )),
        ControlLine('$', (Token(' single ruling'), )),
    ))

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
