from typing import Sequence

import pytest  # pyre-ignore[21]

from ebl.corpus.domain.chapter import (
    Chapter,
    Classification,
    Line,
    LineVariant,
    ManuscriptLine,
    Stage,
)
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
    Siglum,
)
from ebl.corpus.domain.text import Text, TextId
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.transliteration.domain.atf import Ruling, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, Label, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine, StringPart
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word


CATEGORY = 1
INDEX = 2
NAME = "Palm & Vine"
VERSES = 100
APPROXIMATE = True
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
VERSION = "A"
CHAPTER_NAME = "IIc"
ORDER = 1
MANUSCRIPT_ID = 9001
SIGLUM_DISAMBIGUATOR = "1c"
MUSEUM_NUMBER = MuseumNumber("BM", "x")
ACCESSION = ""
PERIOD_MODIFIER = PeriodModifier.LATE
PERIOD = Period.OLD_BABYLONIAN
PROVENANCE = Provenance.NINEVEH
TYPE = ManuscriptType.LIBRARY
NOTES = "some notes"
REFERENCES = (ReferenceFactory.build(),)  # pyre-ignore[16]
LINE_NUMBER = LineNumber(1)
LINE_RECONSTRUCTION = (AkkadianWord.of((ValueToken.of("buāru"),)),)
IS_SECOND_LINE_OF_PARALLELISM = True
IS_BEGINNING_OF_SECTION = True
LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
MANUSCRIPT_TEXT = TextLine(
    LineNumber(1),
    (
        Word.of(
            [
                Reading.of([ValueToken.of("ku"), BrokenAway.close()]),
                Joiner.hyphen(),
                Reading.of_name("nu"),
                Joiner.hyphen(),
                Reading.of_name("si"),
            ]
        ),
    ),
)
PARATEXT = (NoteLine((StringPart("note"),)), RulingDollarLine(Ruling.SINGLE))
OMITTED_WORDS = (1,)

NOTE = None
LINE_VARIANT = LineVariant(
    LINE_RECONSTRUCTION,
    NOTE,
    (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT, PARATEXT, OMITTED_WORDS),),
)
LINE = Line(
    LINE_NUMBER, (LINE_VARIANT,), IS_SECOND_LINE_OF_PARALLELISM, IS_BEGINNING_OF_SECTION
)

TEXT = Text(
    CATEGORY,
    INDEX,
    NAME,
    VERSES,
    APPROXIMATE,
    (
        Chapter(
            CLASSIFICATION,
            STAGE,
            VERSION,
            CHAPTER_NAME,
            ORDER,
            (
                Manuscript(
                    MANUSCRIPT_ID,
                    SIGLUM_DISAMBIGUATOR,
                    MUSEUM_NUMBER,
                    ACCESSION,
                    PERIOD_MODIFIER,
                    PERIOD,
                    PROVENANCE,
                    TYPE,
                    NOTES,
                    REFERENCES,
                ),
            ),
            (MUSEUM_NUMBER,),
            (LINE,),
        ),
    ),
)


def test_constructor_sets_correct_fields():
    assert TEXT.id == TextId(CATEGORY, INDEX)
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.number_of_verses == VERSES
    assert TEXT.approximate_verses == APPROXIMATE
    assert TEXT.chapters[0].classification == CLASSIFICATION
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].version == VERSION
    assert TEXT.chapters[0].name == CHAPTER_NAME
    assert TEXT.chapters[0].order == ORDER
    assert TEXT.chapters[0].uncertain_fragments == (MUSEUM_NUMBER,)
    assert TEXT.chapters[0].manuscripts[0].id == MANUSCRIPT_ID
    assert TEXT.chapters[0].manuscripts[0].siglum == Siglum(
        PROVENANCE, PERIOD, TYPE, SIGLUM_DISAMBIGUATOR
    )
    assert TEXT.chapters[0].manuscripts[0].siglum_disambiguator == SIGLUM_DISAMBIGUATOR
    assert TEXT.chapters[0].manuscripts[0].museum_number == MUSEUM_NUMBER
    assert TEXT.chapters[0].manuscripts[0].accession == ACCESSION
    assert TEXT.chapters[0].manuscripts[0].period_modifier == PERIOD_MODIFIER
    assert TEXT.chapters[0].manuscripts[0].period == PERIOD
    assert TEXT.chapters[0].manuscripts[0].provenance == PROVENANCE
    assert TEXT.chapters[0].manuscripts[0].type == TYPE
    assert TEXT.chapters[0].manuscripts[0].notes == NOTES
    assert TEXT.chapters[0].manuscripts[0].references == REFERENCES
    assert TEXT.chapters[0].lines[0].number == LINE_NUMBER
    assert TEXT.chapters[0].lines[0].variants[0].reconstruction == LINE_RECONSTRUCTION
    assert TEXT.chapters[0].lines[0].variants[0].note == NOTE
    assert (
        TEXT.chapters[0].lines[0].variants[0].manuscripts[0].manuscript_id
        == MANUSCRIPT_ID
    )
    assert TEXT.chapters[0].lines[0].variants[0].manuscripts[0].labels == LABELS
    assert TEXT.chapters[0].lines[0].variants[0].manuscripts[0].line == MANUSCRIPT_TEXT
    assert (
        TEXT.chapters[0].lines[0].variants[0].manuscripts[0].omitted_words
        == OMITTED_WORDS
    )
    assert (
        TEXT.chapters[0].lines[0].is_second_line_of_parallelism
        == IS_SECOND_LINE_OF_PARALLELISM
    )
    assert TEXT.chapters[0].lines[0].is_beginning_of_section == IS_BEGINNING_OF_SECTION


def test_giving_museum_number_and_accession_is_invalid():
    with pytest.raises(ValueError):
        Manuscript(
            MANUSCRIPT_ID,
            museum_number=MUSEUM_NUMBER,
            accession="accession not allowed",
        )


def test_duplicate_ids_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            manuscripts=(
                Manuscript(MANUSCRIPT_ID, siglum_disambiguator="a"),
                Manuscript(MANUSCRIPT_ID, siglum_disambiguator="b"),
            )
        )


def test_duplicate_sigla_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            manuscripts=(
                Manuscript(
                    MANUSCRIPT_ID,
                    siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                    period=PERIOD,
                    provenance=PROVENANCE,
                    type=TYPE,
                ),
                Manuscript(
                    MANUSCRIPT_ID + 1,
                    siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                    period=PERIOD,
                    provenance=PROVENANCE,
                    type=TYPE,
                ),
            )
        )


def test_missing_manuscripts_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (
                                ManuscriptLine(
                                    MANUSCRIPT_ID + 1, LABELS, MANUSCRIPT_TEXT
                                ),
                            ),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        )


@pytest.mark.parametrize(
    "make_chapter",
    [
        lambda: Chapter(
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (
                                ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT),
                                ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT),
                            ),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        ),
        lambda: Chapter(
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT),),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
                Line(
                    LineNumber(2),
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT),),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        ),
    ],
)
def test_duplicate_manuscript_line_labels_are_invalid(make_chapter):
    with pytest.raises(ValueError):
        make_chapter()


def test_duplicate_line_numbers_invalid():
    with pytest.raises(ValueError):
        Chapter(lines=(LINE, LINE))


@pytest.mark.parametrize(  # pyre-ignore[56]
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


def test_stage():
    periods = [period.long_name for period in Period]
    stages = [stage.value for stage in Stage]
    assert stages == [*periods, "Standard Babylonian"]


def test_strip_manuscript_alignment():
    word = Word.of([Reading.of_name("ku")], alignment=1)
    manuscript = ManuscriptLine(
        MANUSCRIPT_ID, LABELS, TextLine(LineNumber(1), (word,)), PARATEXT, OMITTED_WORDS
    )
    expected = ManuscriptLine(
        MANUSCRIPT_ID,
        LABELS,
        TextLine(LineNumber(1), (word.set_alignment(None, None),)),
        PARATEXT,
        tuple(),
    )

    assert manuscript.strip_alignments() == expected
