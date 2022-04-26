import pytest

from ebl.corpus.domain.line import LineVariant, ManuscriptLine
from ebl.transliteration.domain.atf import Ruling, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
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


def test_invalid_enclosures():
    with pytest.raises(ValueError):
        LineVariant((AkkadianWord.of((BrokenAway.open(),)),), NOTE, tuple())
