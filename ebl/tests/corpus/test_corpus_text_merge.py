import pytest

from ebl.corpus.text import ManuscriptLine
from ebl.dictionary.word import WordId
from ebl.text.atf import Surface
from ebl.text.labels import SurfaceLabel, ColumnLabel
from ebl.text.line import TextLine
from ebl.text.token import Word


MANUSCRIPT_ID = 1
LABELS = (ColumnLabel.from_int(1),)
LINE = TextLine('1.', (
    Word('kur',
         unique_lemma=(WordId('word1'),),
         alignment=0),
    Word('ra',
         unique_lemma=(WordId('word2'),),
         alignment=1)
))

NEW_MANUSCRIPT_ID = 2
NEW_LABELS = (SurfaceLabel.from_label(Surface.REVERSE),)
NEW_LINE = TextLine('1.', (Word('kur'), Word('pa')))


@pytest.mark.parametrize('old,new,expected', [
    (
            ManuscriptLine(MANUSCRIPT_ID, LABELS, LINE),
            ManuscriptLine(MANUSCRIPT_ID, LABELS, LINE),
            ManuscriptLine(MANUSCRIPT_ID, LABELS, LINE)
    ),
    (
            ManuscriptLine(MANUSCRIPT_ID, LABELS, LINE),
            ManuscriptLine(NEW_MANUSCRIPT_ID, NEW_LABELS, NEW_LINE),
            ManuscriptLine(NEW_MANUSCRIPT_ID, NEW_LABELS,
                           LINE.merge(NEW_LINE))
    )
])
def test_merge_manuscript_line(old, new, expected):
    assert old.merge(new) == expected
