from typing import Sequence

import pytest

from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.transliteration.domain.atf import Ruling, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, Label, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.word_tokens import Word


LINE_NUMBER = LineNumber(1)
LINE_RECONSTRUCTION = (AkkadianWord.of((ValueToken.of("buāru"),)),)
NOTE = None
MANUSCRIPT_ID = 9001
LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
MANUSCRIPT_TEXT = TextLine(LINE_NUMBER, (Word.of([Reading.of([ValueToken.of("ku")])]),))
PARATEXT = (NoteLine((StringPart("note"),)), RulingDollarLine(Ruling.SINGLE))
OMITTED_WORDS = (1,)
PARALLEL_LINES = (ParallelComposition(False, "a composition", LineNumber(7)),)
INTERTEXT = (StringPart("foo"),)

LINE_VARIANT = LineVariant(
    LINE_RECONSTRUCTION,
    NOTE,
    (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT, PARATEXT, OMITTED_WORDS),),
    PARALLEL_LINES,
    INTERTEXT,
)


def test_invalid_extent() -> None:
    translation = TranslationLine(
        tuple(), extent=Extent(LineNumber(1), (SurfaceLabel(tuple(), Surface.OBVERSE),))
    )

    with pytest.raises(
        ValueError, match="Labels are not allowed in line translations."
    ):
        Line(LineNumber(1), tuple(), translation=(translation,)),


def test_line_variant_constructor():
    assert LINE_VARIANT.reconstruction == LINE_RECONSTRUCTION
    assert LINE_VARIANT.note == NOTE
    assert LINE_VARIANT.parallel_lines == PARALLEL_LINES
    assert LINE_VARIANT.intertext == INTERTEXT
    assert LINE_VARIANT.manuscripts[0].manuscript_id == MANUSCRIPT_ID
    assert LINE_VARIANT.manuscripts[0].labels == LABELS
    assert LINE_VARIANT.manuscripts[0].line == MANUSCRIPT_TEXT
    assert LINE_VARIANT.manuscripts[0].paratext == PARATEXT
    assert LINE_VARIANT.manuscripts[0].omitted_words == OMITTED_WORDS


@pytest.mark.parametrize(
    "labels",
    [
        (ColumnLabel.from_label("i"), ColumnLabel.from_label("ii")),
        (
            SurfaceLabel.from_label(Surface.OBVERSE),
            SurfaceLabel.from_label(Surface.REVERSE),
        ),
        (ColumnLabel.from_label("i"), SurfaceLabel.from_label(Surface.REVERSE)),
    ],
)
def test_invalid_labels(labels: Sequence[Label]):
    with pytest.raises(ValueError):
        ManuscriptLine(manuscript_id=1, labels=labels, line=TextLine(LineNumber(1)))


def test_invalid_reconstruction():
    with pytest.raises(ValueError):
        Line(
            LINE_NUMBER,
            (LineVariant((AkkadianWord.of((BrokenAway.open(),)),), NOTE, tuple()),),
            False,
            False,
        )


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
        MANUSCRIPT_ID,
        LABELS,
        TextLine(LineNumber(1), (word1, word2, word3)),
        PARATEXT,
        (1, 3),
    )
    expected = ManuscriptLine(
        MANUSCRIPT_ID,
        LABELS,
        TextLine(
            LineNumber(1),
            (
                word1.set_alignment(None, None),
                word2.set_alignment(0, word2.variant),
                word3.set_alignment(None, None),
            ),
        ),
        PARATEXT,
        (0,),
    )

    assert manuscript.update_alignments([None, 0]) == expected
