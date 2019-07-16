import pytest

from ebl.corpus.text import ManuscriptLine, Line
from ebl.dictionary.word import WordId
from ebl.text.atf import Surface
from ebl.text.labels import SurfaceLabel, ColumnLabel, LineNumberLabel
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
    ),
])
def test_merge_line(old, new, expected):
    assert old.merge(new) == expected
