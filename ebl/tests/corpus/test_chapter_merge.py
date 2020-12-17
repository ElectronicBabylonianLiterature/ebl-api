import attr
import pytest  # pyre-ignore[21]

from ebl.corpus.domain.chapter import (
    Chapter,
    Classification,
    Line,
    LineVariant,
    ManuscriptLine,
    Stage,
)
from ebl.corpus.domain.manuscript import Manuscript
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine, StringPart
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word


MANUSCRIPT_ID = 1
LABELS = (ColumnLabel.from_int(1),)
TEXT_LINE = TextLine(
    LineNumber(1),
    (
        Word.of([Reading.of_name("kur")], unique_lemma=(WordId("word1"),), alignment=0),
        Word.of([Reading.of_name("ra")], unique_lemma=(WordId("word2"),), alignment=1),
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


RECONSTRUCTION = TextLine.of_iterable(
    LineNumber(1), (AkkadianWord.of((ValueToken.of("buāru"),)),)
)

IS_SECOND_LINE_OF_PARALLELISM = True
IS_BEGINNING_OF_SECTION = True
NOTE = None
LINE = Line(
    (LineVariant(RECONSTRUCTION, NOTE, (MANUSCRIPT_LINE,)),),
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


@pytest.mark.parametrize(  # pyre-ignore[56]
    "old,new,expected",
    [
        (LINE, LINE, LINE),
        (
            Line(
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
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                (
                    LineVariant(
                        TextLine.of_iterable(
                            LineNumber(2), (AkkadianWord.of((ValueToken.of("kur"),)),)
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
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                (
                    LineVariant(
                        TextLine.of_iterable(
                            LineNumber(2), (AkkadianWord.of((ValueToken.of("kur"),)),)
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
                                            alignment=None,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(
                (LineVariant(RECONSTRUCTION, NOTE, (MANUSCRIPT_LINE,)),),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                (
                    LineVariant(
                        TextLine.of_iterable(LineNumber(2), RECONSTRUCTION.content),
                        NOTE,
                        (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
                    ),
                ),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                (
                    LineVariant(
                        TextLine.of_iterable(LineNumber(2), RECONSTRUCTION.content),
                        NOTE,
                        (
                            ManuscriptLine(
                                MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                            ),
                        ),
                    ),
                ),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(
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
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
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
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
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
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
        (
            Line(
                (LineVariant(RECONSTRUCTION, NOTE, tuple()),),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line((LineVariant(RECONSTRUCTION, NOTE, tuple()),), True, True),
            Line((LineVariant(RECONSTRUCTION, NOTE, tuple()),), True, True),
        ),
        (
            Line(
                (
                    LineVariant(
                        RECONSTRUCTION, NoteLine((StringPart("a note"),)), tuple()
                    ),
                ),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                (
                    LineVariant(
                        RECONSTRUCTION, NoteLine((StringPart("new note"),)), tuple()
                    ),
                ),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
            Line(
                (
                    LineVariant(
                        RECONSTRUCTION, NoteLine((StringPart("new note"),)), tuple()
                    ),
                ),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
            ),
        ),
    ],
)
def test_merge_line(old, new, expected) -> None:
    assert old.merge(new) == expected


CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
VERSION = "A"
CHAPTER_NAME = "I"
ORDER = 1
MANUSCRIPT = Manuscript(MANUSCRIPT_ID)
CHAPTER = Chapter(
    CLASSIFICATION, STAGE, VERSION, CHAPTER_NAME, ORDER, (MANUSCRIPT,), (LINE,)
)

NEW_CLASSIFICATION = Classification.MODERN
NEW_STAGE = Stage.MIDDLE_ASSYRIAN
NEW_VERSION = "B"
NEW_CHAPTER_NAME = "II"
NEW_ORDER = 2
NEW_MANUSCRIPT = Manuscript(2, siglum_disambiguator="b")
NOTE = NoteLine((StringPart("a note"),))
NEW_LINE = Line(
    (
        LineVariant(
            RECONSTRUCTION,
            NOTE,
            (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
        ),
    ),
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)
ANOTHER_NEW_LINE = Line(
    (
        LineVariant(
            attr.evolve(RECONSTRUCTION, line_number=LineNumber(2)),
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
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)
NEW_PARATEXT = Line(
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
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)
OLD_LINE = Line(
    (
        LineVariant(
            TextLine.of_iterable(LineNumber(2), tuple()),
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
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (CHAPTER, CHAPTER, CHAPTER),
        (
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (LINE,),
            ),
            Chapter(
                NEW_CLASSIFICATION,
                NEW_STAGE,
                NEW_VERSION,
                NEW_CHAPTER_NAME,
                NEW_ORDER,
                (MANUSCRIPT, NEW_MANUSCRIPT),
                (LINE,),
            ),
            Chapter(
                NEW_CLASSIFICATION,
                NEW_STAGE,
                NEW_VERSION,
                NEW_CHAPTER_NAME,
                NEW_ORDER,
                (MANUSCRIPT, NEW_MANUSCRIPT),
                (LINE,),
            ),
        ),
        (
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (OLD_LINE, LINE),
            ),
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (NEW_LINE, ANOTHER_NEW_LINE),
            ),
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (OLD_LINE.merge(NEW_LINE), LINE.merge(ANOTHER_NEW_LINE)),
            ),
        ),
        (
            CHAPTER,
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (NEW_PARATEXT,),
            ),
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (NEW_PARATEXT,),
            ),
        ),
    ],
)
def test_merge_chapter(old, new, expected):
    assert old.merge(new) == expected
