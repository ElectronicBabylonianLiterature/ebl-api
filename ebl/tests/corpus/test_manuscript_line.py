import pytest

from ebl.tests.factories.corpus import ManuscriptLineFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import StateDollarLine
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.markup import StringPart


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


@pytest.mark.parametrize(  # pyre-ignore[56]
    "paratext,is_end",
    [
        (tuple(), False),
        ((NoteLine((StringPart("note"),)),), False),
        ((StateDollarLine(None, atf.Extent.SEVERAL, None, None, None),), False),
        ((StateDollarLine(None, atf.Extent.END_OF, None, None, None),), True),
        (
            (
                StateDollarLine(None, atf.Extent.SEVERAL, None, None, None),
                StateDollarLine(None, atf.Extent.END_OF, None, None, None),
            ),
            True,
        ),
    ],
)
def test_is_end_of_side(paratext, is_end) -> None:
    line = ManuscriptLineFactory.build(line=EmptyLine(), paratext=paratext)
    assert line.is_end_of_side is is_end
