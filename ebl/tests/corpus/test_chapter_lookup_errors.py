import pytest

from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.errors import NotFoundError
from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.line import EmptyLine


def test_get_manuscript_returns_the_manuscript_with_the_given_id() -> None:
    manuscript = ManuscriptFactory.build(id=7)
    chapter = ChapterFactory.build(manuscripts=(manuscript,), lines=())

    assert chapter.get_manuscript(7) is manuscript


def test_get_manuscript_reports_an_unknown_id() -> None:
    chapter = ChapterFactory.build(
        manuscripts=(ManuscriptFactory.build(id=7),), lines=()
    )

    with pytest.raises(NotFoundError, match="No manuscripts with id 8."):
        chapter.get_manuscript(8)


def test_get_manuscript_reports_an_unknown_id_on_a_chapter_with_no_manuscripts() -> (
    None
):
    chapter = ChapterFactory.build(manuscripts=(), lines=())

    with pytest.raises(NotFoundError, match="No manuscripts with id 1."):
        chapter.get_manuscript(1)


def test_an_empty_manuscript_line_has_no_atf() -> None:
    manuscript_line = ManuscriptLine(manuscript_id=1, labels=(), line=EmptyLine())

    def fail_if_called(_id: int):
        raise AssertionError("the manuscript must not be looked up for an empty line")

    assert manuscript_line.is_empty is True
    assert manuscript_line.get_atf(fail_if_called) == Atf("")
