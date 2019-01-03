from typing import Tuple
from ebl.text.lemmatization import Lemmatization
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
    assert TEXT.lemmatization == Lemmatization.from_list([
        [{'value': 'ha-am', 'uniqueLemma': []}],
        [{'value': ' single ruling'}]
    ])
