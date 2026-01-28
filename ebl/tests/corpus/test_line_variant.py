from typing import Sequence
import attr
import pytest

from ebl.corpus.domain.line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.tests.factories.corpus import (
    LineVariantFactory,
    ManuscriptLineFactory,
)
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
from ebl.transliteration.domain.word_tokens import AbstractWord, Word


LINE_NUMBER = LineNumber(1)
LINE_RECONSTRUCTION = (AkkadianWord.of((ValueToken.of("buāru"),)),)
NOTE = None
MANUSCRIPT_ID = 9001
LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
WORD = Word.of([Reading.of_name("ku")])
MANUSCRIPT_TEXT = TextLine(LINE_NUMBER, (WORD,))
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


def test_line_variant_constructor() -> None:
    assert LINE_VARIANT.reconstruction == LINE_RECONSTRUCTION
    assert LINE_VARIANT.note == NOTE
    assert LINE_VARIANT.parallel_lines == PARALLEL_LINES
    assert LINE_VARIANT.intertext == INTERTEXT
    assert LINE_VARIANT.manuscripts[0].manuscript_id == MANUSCRIPT_ID
    assert LINE_VARIANT.manuscripts[0].labels == LABELS
    assert LINE_VARIANT.manuscripts[0].line == MANUSCRIPT_TEXT
    assert LINE_VARIANT.manuscripts[0].paratext == PARATEXT
    assert LINE_VARIANT.manuscripts[0].omitted_words == OMITTED_WORDS


def test_invalid_enclosures() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        LineVariant((AkkadianWord.of((BrokenAway.open(),)),), NOTE, ())


@pytest.mark.parametrize(
    "word,expected",
    [
        (
            attr.evolve(
                WORD,
                alignment=0,
                variant=Word.of((Reading.of_name("kur"),)),
            ),
            True,
        ),
        (
            attr.evolve(
                WORD,
                alignment=0,
                variant=None,
            ),
            False,
        ),
        (
            attr.evolve(
                WORD,
                alignment=1,
                variant=Word.of((Reading.of_name("ra"),)),
            ),
            False,
        ),
    ],
)
def test_set_has_variant_alignment(word: AbstractWord, expected: bool) -> None:
    aligned_manuscript_text = TextLine(LINE_NUMBER, (word,))
    line_variant = LineVariant(
        LINE_RECONSTRUCTION,
        NOTE,
        (ManuscriptLineFactory.build(line=aligned_manuscript_text),),
        PARALLEL_LINES,
        INTERTEXT,
    )
    expected_reconstruction = (
        AkkadianWord.of((ValueToken.of("buāru"),), has_variant_alignment=expected),
    )
    expected_variant = attr.evolve(line_variant, reconstruction=expected_reconstruction)
    assert line_variant.set_has_variant_alignment() == expected_variant


@pytest.mark.parametrize(
    "omitted_words,expected",
    [
        ((), (False, False, False)),
        ((1, 2), (False, True, True)),
    ],
)
def test_set_has_omitted_alignment(
    omitted_words: Sequence[int], expected: Sequence[bool]
) -> None:
    manuscript_line = ManuscriptLineFactory.build(omitted_words=omitted_words)
    line_variant = LineVariantFactory.build(
        reconstruction=(WORD, WORD, WORD),
        manuscripts=(manuscript_line,),
    )

    assert (
        tuple(
            token.has_omitted_alignment
            for token in line_variant.set_has_omitted_alignment().reconstruction
        )
        == expected
    )
