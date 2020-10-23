import pytest  # pyre-ignore[21]

from ebl.corpus.domain.enums import Classification, Stage
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.note_line import NoteLine, StringPart
import attr

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
    RECONSTRUCTION,
    NOTE,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    (MANUSCRIPT_LINE,),
)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (LINE, LINE, LINE),
        (
            Line(
                RECONSTRUCTION,
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
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
                                            [ValueToken.of("ku"), BrokenAway.close()]
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
            Line(
                TextLine.of_iterable(
                    LineNumber(2), (AkkadianWord.of((ValueToken.of("kur"),)),)
                ),
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
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
                                            [ValueToken.of("ku"), BrokenAway.close()]
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
            Line(
                TextLine.of_iterable(
                    LineNumber(2), (AkkadianWord.of((ValueToken.of("kur"),)),)
                ),
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
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
                                            [ValueToken.of("ku"), BrokenAway.close()]
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
        (
            Line(
                RECONSTRUCTION,
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                (MANUSCRIPT_LINE,),
            ),
            Line(
                TextLine.of_iterable(LineNumber(2), RECONSTRUCTION.content),
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
            ),
            Line(
                TextLine.of_iterable(LineNumber(2), RECONSTRUCTION.content),
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                (
                    ManuscriptLine(
                        MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                    ),
                ),
            ),
        ),
        (
            Line(
                RECONSTRUCTION,
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
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
                                            [ValueToken.of("ku"), BrokenAway.close()]
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
            Line(
                RECONSTRUCTION,
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                (
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                ),
            ),
            Line(
                RECONSTRUCTION,
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                (
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                    ManuscriptLine(
                        MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                    ),
                ),
            ),
        ),
        (
            Line(
                RECONSTRUCTION,
                NOTE,
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                tuple(),
            ),
            Line(RECONSTRUCTION, NOTE, True, True, tuple()),
            Line(RECONSTRUCTION, NOTE, True, True, tuple()),
        ),
        (
            Line(
                RECONSTRUCTION,
                NoteLine((StringPart("a note"),)),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                tuple(),
            ),
            Line(
                RECONSTRUCTION,
                NoteLine((StringPart("new note"),)),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                tuple(),
            ),
            Line(
                RECONSTRUCTION,
                NoteLine((StringPart("new note"),)),
                IS_SECOND_LINE_OF_PARALLELISM,
                IS_BEGINNING_OF_SECTION,
                tuple(),
            ),
        ),
    ],
)
def test_merge_line(old, new, expected):
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
    RECONSTRUCTION,
    NOTE,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
)
ANOTHER_NEW_LINE = Line(
    attr.evolve(RECONSTRUCTION, line_number=LineNumber(2)),
    NOTE,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
)
NEW_PARATEXT = Line(
    RECONSTRUCTION,
    NOTE,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    (
        ManuscriptLine(
            MANUSCRIPT_ID, LABELS, TEXT_LINE, (NoteLine((StringPart("paratext"),)),)
        ),
    ),
)
OLD_LINE = Line(
    TextLine.of_iterable(LineNumber(2), tuple()),
    None,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    (MANUSCRIPT_LINE,),
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
