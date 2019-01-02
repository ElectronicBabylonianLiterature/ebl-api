from typing import Tuple
from ebl.text.line import Line, TextLine
from ebl.text.text import Text
from ebl.text.token import Word


LINES: Tuple[Line, ...] = (
    TextLine('1.', (Word('ha-am'), )),
)
TEXT: Text = Text(LINES)


def test_lines():
    assert TEXT.lines == LINES


def test_to_dict():
    assert TEXT.to_dict() == {
        'lines': [line.to_dict() for line in LINES]
    }
