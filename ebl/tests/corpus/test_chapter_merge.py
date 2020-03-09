import pytest

from ebl.corpus.domain.enums import Classification, Stage
from ebl.corpus.domain.reconstructed_text import AkkadianWord, StringPart
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import (
    ColumnLabel,
    LineNumberLabel,
    SurfaceLabel,
)
from ebl.transliteration.domain.line import TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word

MANUSCRIPT_ID = 1
LABELS = (ColumnLabel.from_int(1),)
TEXT_LINE = TextLine(
    "1.",
    (
        Word.of([Reading.of_name("kur")], unique_lemma=(WordId("word1"),), alignment=0),
        Word.of([Reading.of_name("ra")], unique_lemma=(WordId("word2"),), alignment=1),
    ),
)

NEW_MANUSCRIPT_ID = 2
NEW_LABELS = (SurfaceLabel.from_label(Surface.REVERSE),)
NEW_TEXT_LINE = TextLine(
    "1.", (Word.of([Reading.of_name("kur")]), Word.of([Reading.of_name("pa")]))
)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
        ),
        (
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
            ManuscriptLine(NEW_MANUSCRIPT_ID, NEW_LABELS, NEW_TEXT_LINE),
            ManuscriptLine(
                NEW_MANUSCRIPT_ID, NEW_LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
            ),
        ),
    ],
)
def test_merge_manuscript_line(old, new, expected):
    assert old.merge(new) == expected


LINE_NUMBER = LineNumberLabel("1")
LINE_RECONSTRUCTION = (AkkadianWord((StringPart("buāru"),)),)
LINE = Line(
    LINE_NUMBER,
    LINE_RECONSTRUCTION,
    (ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),),
)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (LINE, LINE, LINE),
        (
            Line(
                LINE_NUMBER,
                LINE_RECONSTRUCTION,
                (
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            "1.",
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
                LineNumberLabel("2"),
                (AkkadianWord((StringPart("kur"),)),),
                (
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            "1.",
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
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            Line(
                LineNumberLabel("2"),
                (AkkadianWord((StringPart("kur"),)),),
                (
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            "1.",
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
                LINE_NUMBER,
                LINE_RECONSTRUCTION,
                (ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),),
            ),
            Line(
                LineNumberLabel("2"),
                LINE_RECONSTRUCTION,
                (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
            ),
            Line(
                LineNumberLabel("2"),
                LINE_RECONSTRUCTION,
                (
                    ManuscriptLine(
                        MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                    ),
                ),
            ),
        ),
        (
            Line(
                LINE_NUMBER,
                LINE_RECONSTRUCTION,
                (
                    ManuscriptLine(
                        MANUSCRIPT_ID,
                        LABELS,
                        TextLine(
                            "1.",
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
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
                ),
            ),
            Line(
                LINE_NUMBER,
                LINE_RECONSTRUCTION,
                (
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                ),
            ),
            Line(
                LINE_NUMBER,
                LINE_RECONSTRUCTION,
                (
                    ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                    ManuscriptLine(
                        MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                    ),
                ),
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
NEW_LINE = Line(
    LINE_NUMBER,
    LINE_RECONSTRUCTION,
    (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
)
OLD_LINE = Line(
    LineNumberLabel("1'"), tuple(), (ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),),
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
                (
                    Line(
                        LineNumberLabel("1'"),
                        tuple(),
                        (ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),),
                    ),
                    LINE,
                ),
            ),
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (NEW_LINE, NEW_LINE),
            ),
            Chapter(
                CLASSIFICATION,
                STAGE,
                VERSION,
                CHAPTER_NAME,
                ORDER,
                (MANUSCRIPT,),
                (OLD_LINE.merge(NEW_LINE), LINE.merge(NEW_LINE)),
            ),
        ),
    ],
)
def test_merge_chapter(old, new, expected):
    assert old.merge(new) == expected
