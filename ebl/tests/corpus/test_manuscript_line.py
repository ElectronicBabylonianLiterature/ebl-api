from typing import Sequence, Union

import attr
import pytest

from ebl.corpus.domain.line import ManuscriptLine
from ebl.tests.factories.corpus import ManuscriptLineFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import DollarLine, StateDollarLine
from ebl.transliteration.domain.labels import ColumnLabel, Label, SurfaceLabel
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


@pytest.mark.parametrize(  # pyre-ignore[56]
    "labels",
    [
        (ColumnLabel.from_label("i"), ColumnLabel.from_label("ii")),
        (
            SurfaceLabel.from_label(atf.Surface.OBVERSE),
            SurfaceLabel.from_label(atf.Surface.REVERSE),
        ),
        (ColumnLabel.from_label("i"), SurfaceLabel.from_label(atf.Surface.REVERSE)),
    ],
)
def test_invalid_labels(labels: Sequence[Label]) -> None:
    with pytest.raises(ValueError):
        ManuscriptLine(manuscript_id=1, labels=labels, line=TextLine(LineNumber(1)))


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
def test_is_end_of_side(
    paratext: Sequence[Union[DollarLine, NoteLine]], is_end: bool
) -> None:
    line = ManuscriptLineFactory.build(line=EmptyLine(), paratext=paratext)
    assert line.is_end_of_side is is_end


def test_update_manuscript_alignment():
    word1 = Word.of(
        [Reading.of_name("ku")], alignment=0, variant=Word.of([Reading.of_name("uk")])
    )
    word2 = Word.of(
        [Reading.of_name("ra")], alignment=1, variant=Word.of([Reading.of_name("ar")])
    )
    word3 = Word.of(
        [Reading.of_name("pa")], alignment=2, variant=Word.of([Reading.of_name("ap")])
    )
    manuscript = ManuscriptLine(
        9001,
        tuple(),
        TextLine(LineNumber(1), (word1, word2, word3)),
        tuple(),
        (1, 3),
    )
    expected = attr.evolve(
        manuscript,
        line=TextLine(
            LineNumber(1),
            (
                word1.set_alignment(None, None),
                word2.set_alignment(0, word2.variant),
                word3.set_alignment(None, None),
            ),
        ),
        omitted_words=(0,),
    )

    assert manuscript.update_alignments([None, 0]) == expected
