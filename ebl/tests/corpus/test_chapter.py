import attr
import pytest
from ebl.common.domain.period import Period, PeriodModifier

from ebl.corpus.domain.chapter import (
    Chapter,
    Classification,
    ExtantLine,
    TextLineEntry,
)
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import (
    Manuscript,
    Siglum,
)
from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.common.domain.provenance import Provenance
from ebl.corpus.domain.record import Author, AuthorRole, Record, Translator
from ebl.transliteration.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import OldSiglumFactory
from ebl.transliteration.domain.atf import Ruling, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import UnknownNumberOfSigns, ValueToken
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.word_tokens import Word


GENRE = Genre.LITERATURE
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
OLD_SIGLA = (OldSiglumFactory.build(),)
MUSEUM_NUMBER = MuseumNumber("BM", "x")
ACCESSION = ""
PERIOD_MODIFIER = PeriodModifier.LATE
PERIOD = Period.OLD_BABYLONIAN
PROVENANCE = Provenance.NINEVEH
TYPE = ManuscriptType.LIBRARY
NOTES = "some notes"
COLOPHON = Transliteration.of_iterable(
    [TextLine(LineNumber(1, True), (Word.of([Reading.of_name("ku")]),))]
)
UNPLACED_LINES = Transliteration.of_iterable(
    [TextLine(LineNumber(4, True), (Word.of([Reading.of_name("bu")]),))]
)
REFERENCES = (ReferenceFactory.build(),)
LINE_NUMBER = LineNumber(1)
OLD_LINE_NUMBERS = tuple()
LINE_RECONSTRUCTION = (AkkadianWord.of((ValueToken.of("buāru"),)),)
IS_SECOND_LINE_OF_PARALLELISM = True
IS_BEGINNING_OF_SECTION = True
LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
PARATEXT = (NoteLine((StringPart("note"),)), RulingDollarLine(Ruling.SINGLE))
OMITTED_WORDS = (1,)

NOTE = None
PARALLEL_LINES = (ParallelComposition(False, "a composition", LineNumber(7)),)
TRANSLATION = (TranslationLine((StringPart("foo"),), "en", None),)
SIGNS = ("FOO BAR",)

MANUSCRIPT_TEXT_1 = TextLine(
    LineNumber(1), (Word.of([Reading.of([ValueToken.of("ku")])]),)
)

LINE_VARIANT_1 = LineVariant(
    LINE_RECONSTRUCTION,
    NOTE,
    (
        ManuscriptLine(
            MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1, PARATEXT, OMITTED_WORDS
        ),
    ),
    PARALLEL_LINES,
)
LINE_1 = Line(
    LINE_NUMBER,
    (LINE_VARIANT_1,),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    TRANSLATION,
)

LINE_VARIANT_2 = LineVariant(
    LINE_RECONSTRUCTION, None, (ManuscriptLine(MANUSCRIPT_ID, tuple(), EmptyLine()),)
)
LINE_2 = Line(LineNumber(2), (LINE_VARIANT_2,))

MANUSCRIPT_TEXT_3 = attr.evolve(MANUSCRIPT_TEXT_1, line_number=LineNumber(3))
LINE_VARIANT_3 = LineVariant(
    LINE_RECONSTRUCTION,
    None,
    (ManuscriptLine(MANUSCRIPT_ID, tuple(), MANUSCRIPT_TEXT_3),),
)
LINE_3 = Line(LineNumber(3), (LINE_VARIANT_3,))

RECORD = Record(
    (Author("Author", "Test", AuthorRole.EDITOR, ""),),
    (Translator("Author", "Test", "", "en"),),
    "",
)

TEXT_ID = TextId(GENRE, CATEGORY, INDEX)
CHAPTER = Chapter(
    TEXT_ID,
    CLASSIFICATION,
    STAGE,
    VERSION,
    CHAPTER_NAME,
    ORDER,
    (
        Manuscript(
            MANUSCRIPT_ID,
            SIGLUM_DISAMBIGUATOR,
            OLD_SIGLA,
            MUSEUM_NUMBER,
            ACCESSION,
            PERIOD_MODIFIER,
            PERIOD,
            PROVENANCE,
            TYPE,
            NOTES,
            COLOPHON,
            UNPLACED_LINES,
            REFERENCES,
        ),
    ),
    (MUSEUM_NUMBER,),
    (LINE_1, LINE_2, LINE_3),
    SIGNS,
    RECORD,
)


def test_constructor_sets_correct_fields():
    assert CHAPTER.text_id == TextId(GENRE, CATEGORY, INDEX)
    assert CHAPTER.classification == CLASSIFICATION
    assert CHAPTER.stage == STAGE
    assert CHAPTER.version == VERSION
    assert CHAPTER.name == CHAPTER_NAME
    assert CHAPTER.order == ORDER
    assert CHAPTER.uncertain_fragments == (MUSEUM_NUMBER,)
    assert CHAPTER.manuscripts[0].id == MANUSCRIPT_ID
    assert CHAPTER.manuscripts[0].siglum == Siglum(
        PROVENANCE, PERIOD, TYPE, SIGLUM_DISAMBIGUATOR
    )
    assert CHAPTER.manuscripts[0].siglum_disambiguator == SIGLUM_DISAMBIGUATOR
    assert CHAPTER.manuscripts[0].old_sigla == OLD_SIGLA
    assert CHAPTER.manuscripts[0].museum_number == MUSEUM_NUMBER
    assert CHAPTER.manuscripts[0].accession == ACCESSION
    assert CHAPTER.manuscripts[0].period_modifier == PERIOD_MODIFIER
    assert CHAPTER.manuscripts[0].period == PERIOD
    assert CHAPTER.manuscripts[0].provenance == PROVENANCE
    assert CHAPTER.manuscripts[0].type == TYPE
    assert CHAPTER.manuscripts[0].notes == NOTES
    assert CHAPTER.manuscripts[0].colophon == COLOPHON
    assert CHAPTER.manuscripts[0].unplaced_lines == UNPLACED_LINES
    assert CHAPTER.manuscripts[0].references == REFERENCES
    assert CHAPTER.lines[0].number == LINE_NUMBER
    assert CHAPTER.lines[0].variants == (LINE_VARIANT_1,)
    assert (
        CHAPTER.lines[0].is_second_line_of_parallelism == IS_SECOND_LINE_OF_PARALLELISM
    )
    assert CHAPTER.lines[0].is_beginning_of_section == IS_BEGINNING_OF_SECTION
    assert CHAPTER.lines[0].translation == TRANSLATION
    assert CHAPTER.signs == SIGNS
    assert CHAPTER.record == RECORD


def test_duplicate_ids_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            TEXT_ID,
            manuscripts=(
                Manuscript(MANUSCRIPT_ID, siglum_disambiguator="a"),
                Manuscript(MANUSCRIPT_ID, siglum_disambiguator="b"),
            ),
        )


def test_duplicate_sigla_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            TEXT_ID,
            manuscripts=(
                Manuscript(
                    MANUSCRIPT_ID,
                    siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                    old_sigla=OLD_SIGLA,
                    period=PERIOD,
                    provenance=PROVENANCE,
                    type=TYPE,
                ),
                Manuscript(
                    MANUSCRIPT_ID + 1,
                    siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                    old_sigla=OLD_SIGLA,
                    period=PERIOD,
                    provenance=PROVENANCE,
                    type=TYPE,
                ),
            ),
        )


def test_missing_manuscripts_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            TEXT_ID,
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
                                    MANUSCRIPT_ID + 1, LABELS, MANUSCRIPT_TEXT_1
                                ),
                            ),
                        ),
                    ),
                    OLD_LINE_NUMBERS,
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        )


@pytest.mark.parametrize(
    "make_chapter",
    [
        lambda: Chapter(
            TEXT_ID,
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
                                    MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1
                                ),
                                ManuscriptLine(
                                    MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1
                                ),
                            ),
                        ),
                    ),
                    OLD_LINE_NUMBERS,
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        ),
        lambda: Chapter(
            TEXT_ID,
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1),),
                        ),
                    ),
                    OLD_LINE_NUMBERS,
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
                Line(
                    LineNumber(2),
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1),),
                        ),
                    ),
                    OLD_LINE_NUMBERS,
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
        Chapter(TEXT_ID, lines=(LINE_1, LINE_1))


def test_stage():
    periods = [period.long_name for period in Period if period is not Period.NONE]
    stages = [stage.long_name for stage in Stage]
    assert stages == [*periods, "Standard Babylonian"]


def test_text_lines() -> None:
    assert CHAPTER.text_lines == [
        [
            TextLineEntry(MANUSCRIPT_TEXT_1, 0),
            TextLineEntry(MANUSCRIPT_TEXT_3, 2),
            *[TextLineEntry(line, None) for line in COLOPHON.text_lines],
            *[TextLineEntry(line, None) for line in UNPLACED_LINES.text_lines],
        ]
    ]


def test_invalid_extent() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        Chapter(
            TextId(GENRE, 0, 0),
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LineNumber(1),
                    (LINE_VARIANT_1,),
                    translation=(
                        TranslationLine(tuple(), extent=Extent(LineNumber(2))),
                    ),
                ),
            ),
        )


def test_extent_before_translation() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        Chapter(
            TextId(GENRE, 0, 0),
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(LineNumber(1), (LINE_VARIANT_1,)),
                Line(
                    LineNumber(2),
                    (LINE_VARIANT_2,),
                    translation=(
                        TranslationLine(tuple(), extent=Extent(LineNumber(1))),
                    ),
                ),
            ),
        )


def test_overlapping() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        Chapter(
            TextId(GENRE, 0, 0),
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LineNumber(1),
                    (LINE_VARIANT_1,),
                    translation=(
                        TranslationLine(tuple(), extent=Extent(LineNumber(2))),
                    ),
                ),
                Line(
                    LineNumber(2),
                    (LINE_VARIANT_2,),
                    translation=(TranslationLine(tuple()),),
                ),
            ),
        )


def test_overlapping_languages() -> None:
    Chapter(
        TextId(GENRE, 0, 0),
        manuscripts=(Manuscript(MANUSCRIPT_ID),),
        lines=(
            Line(
                LineNumber(1),
                (LINE_VARIANT_1,),
                translation=(TranslationLine(tuple(), "en", Extent(LineNumber(2))),),
            ),
            Line(
                LineNumber(2),
                (LINE_VARIANT_2,),
                translation=(TranslationLine(tuple(), "de"),),
            ),
        ),
    )


def test_extant_lines() -> None:
    manuscript = Manuscript(MANUSCRIPT_ID)
    manuscript_line = LINE_VARIANT_1.manuscripts[0]
    chapter = Chapter(
        TEXT_ID,
        manuscripts=(manuscript,),
        lines=(
            Line(LineNumber(1), (LINE_VARIANT_1,)),
            Line(LineNumber(2), (LINE_VARIANT_2,)),
        ),
    )
    assert chapter.extant_lines == {
        manuscript.siglum: {
            manuscript_line.labels: [
                ExtantLine(manuscript_line.labels, LineNumber(1), True)
            ]
        }
    }


def test_extant_lines_mixed_sides() -> None:
    manuscript = Manuscript(
        MANUSCRIPT_ID,
        siglum_disambiguator="1",
        old_sigla=tuple(),
        period_modifier=PeriodModifier.NONE,
        period=Period.LATE_BABYLONIAN,
        provenance=Provenance.BABYLON,
        type=ManuscriptType.SCHOOL,
    )
    manuscript_line = ManuscriptLine(
        MANUSCRIPT_ID,
        LABELS,
        TextLine(
            LineNumberRange(LineNumber(1), LineNumber(3, suffix_modifier="b")),
            (UnknownNumberOfSigns.of(),),
        ),
        PARATEXT,
        OMITTED_WORDS,
    )
    manuscript_line2 = ManuscriptLine(
        MANUSCRIPT_ID,
        tuple(),
        TextLine(LineNumber(2), (UnknownNumberOfSigns.of(),)),
        PARATEXT,
        OMITTED_WORDS,
    )
    manuscript_line3 = ManuscriptLine(
        MANUSCRIPT_ID,
        LABELS,
        TextLine(LineNumber(3), (UnknownNumberOfSigns.of(),)),
        PARATEXT,
        OMITTED_WORDS,
    )
    chapter = Chapter(
        TEXT_ID,
        manuscripts=(manuscript,),
        lines=(
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        LINE_RECONSTRUCTION, NOTE, (manuscript_line,), PARALLEL_LINES
                    ),
                ),
            ),
            Line(
                LineNumber(2),
                (
                    LineVariant(
                        LINE_RECONSTRUCTION, NOTE, (manuscript_line2,), PARALLEL_LINES
                    ),
                ),
            ),
            Line(
                LineNumber(3),
                (
                    LineVariant(
                        LINE_RECONSTRUCTION, NOTE, (manuscript_line3,), PARALLEL_LINES
                    ),
                ),
            ),
        ),
    )
    assert chapter.extant_lines == {
        manuscript.siglum: {
            manuscript_line.labels: [
                ExtantLine(manuscript_line.labels, LineNumber(1), True),
                ExtantLine(manuscript_line3.labels, LineNumber(3), False),
            ],
            manuscript_line2.labels: [
                ExtantLine(manuscript_line2.labels, LineNumber(2), False)
            ],
        }
    }
