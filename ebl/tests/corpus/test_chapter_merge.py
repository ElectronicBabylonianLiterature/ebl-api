import pytest

from ebl.corpus.enums import Classification, Stage
from ebl.corpus.text import Chapter, Line, Manuscript, ManuscriptLine
from ebl.dictionary.word import WordId
from ebl.text.atf import Surface
from ebl.text.labels import ColumnLabel, LineNumberLabel, SurfaceLabel
from ebl.text.line import TextLine
from ebl.text.reconstructed_text import AkkadianWord, StringPart
from ebl.text.token import Word

MANUSCRIPT_ID = 1
LABELS = (ColumnLabel.from_int(1),)
TEXT_LINE = TextLine('1.', (
    Word('kur',
         unique_lemma=(WordId('word1'),),
         alignment=0),
    Word('ra',
         unique_lemma=(WordId('word2'),),
         alignment=1)
))

NEW_MANUSCRIPT_ID = 2
NEW_LABELS = (SurfaceLabel.from_label(Surface.REVERSE),)
NEW_TEXT_LINE = TextLine('1.', (Word('kur'), Word('pa')))


@pytest.mark.parametrize('old,new,expected', [
    (
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE)
    ),
    (
            ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),
            ManuscriptLine(NEW_MANUSCRIPT_ID, NEW_LABELS, NEW_TEXT_LINE),
            ManuscriptLine(NEW_MANUSCRIPT_ID, NEW_LABELS,
                           TEXT_LINE.merge(NEW_TEXT_LINE))
    )
])
def test_merge_manuscript_line(old, new, expected):
    assert old.merge(new) == expected


LINE_NUMBER = LineNumberLabel('1')
LINE_RECONSTRUCTION = (AkkadianWord((StringPart('buāru'),)),)
LINE = Line(LINE_NUMBER, LINE_RECONSTRUCTION,
            (ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),))


@pytest.mark.parametrize('old,new,expected', [
    (
            LINE,
            LINE,
            LINE
    ),
    (
            Line(LINE_NUMBER, LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                 TextLine('1.', (
                                         Word('ku]-nu-ši',
                                              unique_lemma=(WordId('word'),),
                                              alignment=0),
                                 ))),)),
            Line(LineNumberLabel('2'), (AkkadianWord((StringPart('kur'),)),),
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                 TextLine('1.', (
                                         Word('ku]-nu-ši'),
                                 ))),)),
            Line(LineNumberLabel('2'), (AkkadianWord((StringPart('kur'),)),),
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                 TextLine('1.', (
                                         Word('ku]-nu-ši',
                                              unique_lemma=(WordId('word'),),
                                              alignment=None),
                                 ))),))
    ),
    (
            Line(LINE_NUMBER, LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE),)),
            Line(LineNumberLabel('2'), LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),)),
            Line(LineNumberLabel('2'), LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                 TEXT_LINE.merge(NEW_TEXT_LINE)),))
    ),
    (
            Line(LINE_NUMBER, LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                 TextLine('1.', (
                                         Word('ku]-nu-ši',
                                              unique_lemma=(WordId('word'),),
                                              alignment=0),
                                 ))),
                  ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE))),
            Line(LINE_NUMBER, LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                  ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE))),
            Line(LINE_NUMBER, LINE_RECONSTRUCTION,
                 (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                 TEXT_LINE.merge(NEW_TEXT_LINE)),
                  ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE)))
    )
])
def test_merge_line(old, new, expected):
    assert old.merge(new) == expected


CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
VERSION = 'A'
CHAPTER_NAME = 'I'
ORDER = 1
MANUSCRIPT = Manuscript(MANUSCRIPT_ID)
CHAPTER = Chapter(CLASSIFICATION, STAGE, VERSION, CHAPTER_NAME, ORDER,
                  (MANUSCRIPT,), (LINE,))

NEW_CLASSIFICATION = Classification.MODERN
NEW_STAGE = Stage.MIDDLE_ASSYRIAN
NEW_VERSION = 'B'
NEW_CHAPTER_NAME = 'II'
NEW_ORDER = 2
NEW_MANUSCRIPT = Manuscript(2, siglum_disambiguator='b')
NEW_LINE = Line(LINE_NUMBER, LINE_RECONSTRUCTION,
                (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),))


@pytest.mark.parametrize('old,new,expected', [
    (
            CHAPTER,
            CHAPTER,
            CHAPTER
    ),
    (
            Chapter(CLASSIFICATION, STAGE, VERSION, CHAPTER_NAME, ORDER,
                    (MANUSCRIPT,), (LINE,)),
            Chapter(NEW_CLASSIFICATION, NEW_STAGE, NEW_VERSION,
                    NEW_CHAPTER_NAME, NEW_ORDER, (MANUSCRIPT, NEW_MANUSCRIPT),
                    (LINE,)),
            Chapter(NEW_CLASSIFICATION, NEW_STAGE, NEW_VERSION,
                    NEW_CHAPTER_NAME, NEW_ORDER, (MANUSCRIPT, NEW_MANUSCRIPT),
                    (LINE,))
    ),
    (
            Chapter(CLASSIFICATION, STAGE, VERSION, CHAPTER_NAME, ORDER,
                    (MANUSCRIPT,), (Line(LineNumberLabel("1'"), tuple(),
                                         (ManuscriptLine(MANUSCRIPT_ID, LABELS,
                                                         TEXT_LINE),)), LINE)),
            Chapter(CLASSIFICATION, STAGE, VERSION, CHAPTER_NAME, ORDER,
                    (MANUSCRIPT,), (NEW_LINE, NEW_LINE)),
            Chapter(CLASSIFICATION, STAGE, VERSION, CHAPTER_NAME, ORDER,
                    (MANUSCRIPT,), (LINE.merge(NEW_LINE), NEW_LINE)),
    )
])
def test_merge_chapter(old, new, expected):
    assert old.merge(new) == expected
