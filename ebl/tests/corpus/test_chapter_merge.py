import attr
import pytest

from ebl.transliteration.domain.text_id import TextId
from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import Manuscript
from ebl.common.domain.stage import Stage
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Caesura
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.genre import Genre

MANUSCRIPT_ID = 1
LABELS = (ColumnLabel.from_int(1),)
TEXT_LINE = TextLine(
    LineNumber(1),
    (
        Word.of([Reading.of_name("kur")], unique_lemma=(WordId("word1"),), alignment=0),
        Word.of(
            [Reading.of_name("ra")], unique_lemma=(WordId("word2"),), alignment=None
        ),
    ),
)

NEW_MANUSCRIPT_ID = 2
NEW_LABELS = (SurfaceLabel.from_label(Surface.REVERSE),)
NEW_TEXT_LINE = TextLine(
    LineNumber(1), (Word.of([Reading.of_name("kur")]), Word.of([Reading.of_name("pa")]))
)
MANUSCRIPT_LINE = ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (MANUSCRIPT_LINE, MANUSCRIPT_LINE, MANUSCRIPT_LINE),
        (
            MANUSCRIPT_LINE,
            ManuscriptLine(NEW_MANUSCRIPT_ID, NEW_LABELS, NEW_TEXT_LINE),
            ManuscriptLine(
                NEW_MANUSCRIPT_ID, NEW_LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
            ),
        ),
    ],
)
def test_merge_manuscript_line(old, new, expected):
    assert old.merge(new) == expected


RECONSTRUCTION = (
    AkkadianWord.of((ValueToken.of("buāru"),), unique_lemma=(WordId("buāru I"),)),
)
RECONSTRUCTION_WITHOUT_LEMMA = (AkkadianWord.of((ValueToken.of("buāru"),)),)

IS_SECOND_LINE_OF_PARALLELISM = True
IS_BEGINNING_OF_SECTION = True
NOTE = None
OLD_LINE_NUMBERS = ()
LINE = Line(
    LineNumber(1),
    (LineVariant(RECONSTRUCTION, NOTE, (MANUSCRIPT_LINE,)),),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            LineVariant(
                (
                    AkkadianWord.of(
                        (ValueToken.of("buāru"),), has_variant_alignment=True
                    ),
                ),
                manuscripts=(
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            LineNumber(1),
                            (
                                Word.of(
                                    [Reading.of_name("kur")],
                                    alignment=0,
                                    variant=Word.of([Reading.of_name("kur")]),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            LineVariant(
                (
                    AkkadianWord.of(
                        (ValueToken.of("kurkur"),), has_variant_alignment=False
                    ),
                ),
                manuscripts=(
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            LineNumber(1),
                            (
                                Word.of(
                                    [Reading.of_name("kur")],
                                    alignment=None,
                                    variant=None,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            LineVariant(
                (
                    AkkadianWord.of(
                        (ValueToken.of("kurkur"),), has_variant_alignment=True
                    ),
                ),
                manuscripts=(
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            LineNumber(1),
                            (
                                Word.of(
                                    [Reading.of_name("kur")],
                                    alignment=0,
                                    variant=Word.of([Reading.of_name("kur")]),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ],
)
def test_merge_line_variant(old, new, expected):
    assert old.merge(new) == expected


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (LINE, LINE, LINE),
        (
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        RECONSTRUCTION,
                        NOTE,
                        (
                            ManuscriptLine(
                                MANUSCRIPT_ID,
                                LABELS,
                                TextLine(
                                    LineNumber(1),
                                    (
                                        Word.of(
                                            [
                                                Reading.of(
                                                    [
                                                        ValueToken.of("ku"),
                                                        BrokenAway.close(),
                                                    ]
                                                ),
                                                Joiner.hyphen(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("si"),
                                            ],
                                            unique_lemma=(WordId("word"),),
                                            alignment=0,
                                        ),
                                    ),
                                ),
                            ),
                        ),
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
                        (
                            AkkadianWord.of((ValueToken.of("kur"),)),
                            AkkadianWord.of((ValueToken.of("ra"),)),
                        ),
                        NOTE,
                        (
                            ManuscriptLine(
                                MANUSCRIPT_ID,
                                LABELS,
                                TextLine(
                                    LineNumber(1),
                                    (
                                        Word.of(
                                            [
                                                Reading.of(
                                                    [
                                                        ValueToken.of("ku"),
                                                        BrokenAway.close(),
                                                    ]
                                                ),
                                                Joiner.hyphen(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("si"),
                                            ]
                                        ),
                                    ),
                                ),
                            ),
                        ),
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
                        (
                            AkkadianWord.of((ValueToken.of("kur"),)),
                            AkkadianWord.of((ValueToken.of("ra"),)),
                        ),
                        NOTE,
                        (
                            ManuscriptLine(
                                MANUSCRIPT_ID,
                                LABELS,
                                TextLine(
                                    LineNumber(1),
                                    (
                                        Word.of(
                                            [
                                                Reading.of(
                                                    [
                                                        ValueToken.of("ku"),
                                                        BrokenAway.close(),
                                                    ]
                                                ),
                                                Joiner.hyphen(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("si"),
                                            ],
                                            unique_lemma=(WordId("word"),),
                                            alignment=0,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NOTE, (MANUSCRIPT_LINE,)),),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                LineNumber(2),
                (
                    LineVariant(
                        RECONSTRUCTION,
                        NOTE,
                        (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
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
                        RECONSTRUCTION,
                        NOTE,
                        (
                            ManuscriptLine(
                                MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                            ),
                        ),
                    ),
                ),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        RECONSTRUCTION,
                        NOTE,
                        (
                            ManuscriptLine(
                                MANUSCRIPT_ID,
                                LABELS,
                                TextLine(
                                    LineNumber(1),
                                    (
                                        Word.of(
                                            [
                                                Reading.of(
                                                    [
                                                        ValueToken.of("ku"),
                                                        BrokenAway.close(),
                                                    ]
                                                ),
                                                Joiner.hyphen(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("si"),
                                            ],
                                            unique_lemma=(WordId("word"),),
                                            alignment=0,
                                        ),
                                    ),
                                ),
                            ),
                            MANUSCRIPT_LINE,
                        ),
                    ),
                ),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        RECONSTRUCTION,
                        NOTE,
                        (
                            ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                            ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                        ),
                    ),
                ),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        RECONSTRUCTION,
                        NOTE,
                        (
                            ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                            ManuscriptLine(
                                MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                            ),
                        ),
                    ),
                ),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NOTE, ()),),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NOTE, ()),),
                OLD_LINE_NUMBERS,
                True,
                True,
            ),
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NOTE, ()),),
                OLD_LINE_NUMBERS,
                True,
                True,
            ),
        ),
        (
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NoteLine((StringPart("a note"),)), ()),),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NoteLine((StringPart("new note"),)), ()),),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                LineNumber(1),
                (LineVariant(RECONSTRUCTION, NoteLine((StringPart("new note"),)), ()),),
                OLD_LINE_NUMBERS,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(LineNumber(1), (LineVariant(RECONSTRUCTION),)),
            Line(LineNumber(1), (LineVariant(RECONSTRUCTION_WITHOUT_LEMMA),)),
            Line(LineNumber(1), (LineVariant(RECONSTRUCTION),)),
        ),
        (
            Line(
                LineNumber(1), (LineVariant(RECONSTRUCTION, None, (MANUSCRIPT_LINE,)),)
            ),
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        RECONSTRUCTION_WITHOUT_LEMMA,
                        None,
                        (MANUSCRIPT_LINE.update_alignments([]),),
                    ),
                ),
            ),
            Line(
                LineNumber(1), (LineVariant(RECONSTRUCTION, None, (MANUSCRIPT_LINE,)),)
            ),
        ),
        (
            Line(
                LineNumber(1), (LineVariant(RECONSTRUCTION, None, (MANUSCRIPT_LINE,)),)
            ),
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        (Caesura.certain(),),
                        None,
                        (MANUSCRIPT_LINE.update_alignments([]),),
                    ),
                ),
            ),
            Line(
                LineNumber(1),
                (
                    LineVariant(
                        (Caesura.certain(),),
                        None,
                        (MANUSCRIPT_LINE.update_alignments([None]),),
                    ),
                ),
            ),
        ),
    ],
)
def test_merge_line(old: Line, new: Line, expected: Line) -> None:
    assert old.merge(new) == expected


TEXT_ID = TextId(Genre.LITERATURE, 0, 0)
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
VERSION = "A"
CHAPTER_NAME = "I"
ORDER = 1
MANUSCRIPT = Manuscript(MANUSCRIPT_ID)
MUSEUM_NUMBER = MuseumNumber.of("K.1")
CHAPTER = Chapter(
    TEXT_ID,
    CLASSIFICATION,
    STAGE,
    VERSION,
    CHAPTER_NAME,
    ORDER,
    (MANUSCRIPT,),
    (MUSEUM_NUMBER,),
    (LINE,),
)

NEW_CLASSIFICATION = Classification.MODERN
NEW_STAGE = Stage.MIDDLE_ASSYRIAN
NEW_VERSION = "B"
NEW_CHAPTER_NAME = "II"
NEW_ORDER = 2
NEW_MANUSCRIPT = Manuscript(2, siglum_disambiguator="b")
NOTE = NoteLine((StringPart("a note"),))
NEW_LINE = Line(
    LineNumber(1),
    (
        LineVariant(
            RECONSTRUCTION,
            NOTE,
            (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)
ANOTHER_NEW_LINE = Line(
    LineNumber(2),
    (
        LineVariant(
            RECONSTRUCTION,
            NOTE,
            (
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    attr.evolve(NEW_TEXT_LINE, line_number=LineNumber(2)),
                ),
            ),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)
NEW_PARATEXT = Line(
    LineNumber(1),
    (
        LineVariant(
            RECONSTRUCTION,
            NOTE,
            (
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    TEXT_LINE,
                    (NoteLine((StringPart("paratext"),)),),
                ),
            ),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)
OLD_LINE = Line(
    LineNumber(2),
    (
        LineVariant(
            (),
            None,
            (
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    attr.evolve(TEXT_LINE, line_number=LineNumber(2)),
                ),
            ),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (CHAPTER, CHAPTER, CHAPTER),
        (
            Chapter(
                TEXT_ID,
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (MUSEUM_NUMBER,),
                (LINE,),
            ),
            Chapter(
                TEXT_ID,
                NEW_CLASSIFICATION,
                NEW_STAGE,
                NEW_VERSION,
                NEW_CHAPTER_NAME,
                NEW_ORDER,
                (MANUSCRIPT, NEW_MANUSCRIPT),
                (MUSEUM_NUMBER,),
                (LINE,),
            ),
            Chapter(
                TEXT_ID,
                NEW_CLASSIFICATION,
                NEW_STAGE,
                NEW_VERSION,
                NEW_CHAPTER_NAME,
                NEW_ORDER,
                (MANUSCRIPT, NEW_MANUSCRIPT),
                (MUSEUM_NUMBER,),
                (LINE,),
            ),
        ),
        (
            Chapter(
                TEXT_ID,
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (MUSEUM_NUMBER,),
                (OLD_LINE, LINE),
            ),
            Chapter(
                TEXT_ID,
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (),
                (NEW_LINE, ANOTHER_NEW_LINE),
            ),
            Chapter(
                TEXT_ID,
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (),
                (OLD_LINE.merge(NEW_LINE), LINE.merge(ANOTHER_NEW_LINE)),
            ),
        ),
        (
            CHAPTER,
            Chapter(
                TEXT_ID,
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (MUSEUM_NUMBER,),
                (NEW_PARATEXT,),
            ),
            Chapter(
                TEXT_ID,
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (MUSEUM_NUMBER,),
                (NEW_PARATEXT,),
            ),
        ),
    ],
)
def test_merge_chapter(old, new, expected):
    assert old.merge(new) == expected
