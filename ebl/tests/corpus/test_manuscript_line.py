import pytest

from ebl.tests.factories.corpus import ManuscriptLineFactory
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine


@pytest.mark.parametrize(
    "line,is_beginning",
    [
        (EmptyLine(), False),
        (TextLine(LineNumber(2)), False),
        (TextLine(LineNumber(1)), True),
    ],
)
def test_is_beginning_of_side(line, is_beginning) -> None:
    line = ManuscriptLineFactory.build(line=line)
    assert line.is_beginning_of_side is is_beginning
