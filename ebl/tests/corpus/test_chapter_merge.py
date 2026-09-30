import pytest
from ebl.tests.corpus.chapter_merge_cases_1_1 import CHAPTER_MERGE_CASES_1_1
from ebl.tests.corpus.chapter_merge_cases_2_1 import CHAPTER_MERGE_CASES_2_1
from ebl.tests.corpus.chapter_merge_cases_2_2 import CHAPTER_MERGE_CASES_2_2
from ebl.tests.corpus.chapter_merge_cases_3_1 import CHAPTER_MERGE_CASES_3_1
from ebl.tests.corpus.chapter_merge_fixtures import (
    MANUSCRIPT_LINE,
    NEW_LABELS,
    NEW_MANUSCRIPT_ID,
    NEW_TEXT_LINE,
    TEXT_LINE,
)

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine


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


@pytest.mark.parametrize(
    "old,new,expected",
    [
        *CHAPTER_MERGE_CASES_1_1,
    ],
)
def test_merge_line_variant(old, new, expected):
    assert old.merge(new) == expected


@pytest.mark.parametrize(
    "old,new,expected",
    [
        *CHAPTER_MERGE_CASES_2_1,
        *CHAPTER_MERGE_CASES_2_2,
    ],
)
def test_merge_line(old: Line, new: Line, expected: Line) -> None:
    assert old.merge(new) == expected


@pytest.mark.parametrize(
    "old,new,expected",
    [
        *CHAPTER_MERGE_CASES_3_1,
    ],
)
def test_merge_chapter(old, new, expected):
    assert old.merge(new) == expected
