import re
from typing import Optional

import attr
import pytest

from ebl.corpus.application.outline_schemas import load_chapter_outline
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
    require_revision,
)
from ebl.corpus.domain.lines_page import LinesPage
from ebl.errors import ConflictError
from ebl.tests.corpus.outline_support import (
    create_outline_chapter,
    create_outline_document,
    create_provenance_service,
)
from ebl.tests.factories.corpus import ChapterFactory

REVISION = "6aff54f935de52a4db0c81df"
OTHER_REVISION = "6aff54f935de52a4db0c81e0"
CHAPTER = ChapterFactory.build()


def test_legacy_revision() -> None:
    assert LEGACY_REVISION == "legacy"


def test_chapter_revision_conflict() -> None:
    error = chapter_revision_conflict(CHAPTER.id_, REVISION, OTHER_REVISION)

    assert isinstance(error, ConflictError)
    assert str(error) == (
        f"Chapter {CHAPTER.id_} has changed: "
        f"expected revision {REVISION}, found {OTHER_REVISION}."
    )


@pytest.mark.parametrize(
    "expected,actual",
    [
        (None, REVISION),
        (None, LEGACY_REVISION),
        (REVISION, REVISION),
        (LEGACY_REVISION, LEGACY_REVISION),
    ],
)
def test_require_revision_accepts(expected: Optional[str], actual: str) -> None:
    require_revision(CHAPTER.id_, expected, actual)


@pytest.mark.parametrize(
    "expected,actual",
    [
        (REVISION, OTHER_REVISION),
        (REVISION, LEGACY_REVISION),
        (LEGACY_REVISION, REVISION),
        ("", REVISION),
    ],
)
def test_require_revision_rejects(expected: str, actual: str) -> None:
    message = str(chapter_revision_conflict(CHAPTER.id_, expected, actual))

    with pytest.raises(ConflictError, match=re.escape(message)):
        require_revision(CHAPTER.id_, expected, actual)


def test_chapter_outline_of_chapter_is_legacy_by_default() -> None:
    assert ChapterOutline.of_chapter(CHAPTER).revision == LEGACY_REVISION


def test_chapter_outline_of_chapter_with_revision() -> None:
    outline = ChapterOutline.of_chapter(CHAPTER, REVISION)

    assert outline.revision == REVISION
    assert outline == attr.evolve(ChapterOutline.of_chapter(CHAPTER), revision=REVISION)
    assert outline != ChapterOutline.of_chapter(CHAPTER)


def test_load_chapter_outline_without_revision_is_legacy() -> None:
    chapter = create_outline_chapter()
    document = create_outline_document(chapter)

    outline = load_chapter_outline(document, create_provenance_service())

    assert "revision" not in document
    assert outline.revision == LEGACY_REVISION


def test_load_chapter_outline_with_revision() -> None:
    chapter = create_outline_chapter()
    document = {**create_outline_document(chapter), "revision": REVISION}

    outline = load_chapter_outline(document, create_provenance_service())

    assert outline == ChapterOutline.of_chapter(chapter, REVISION)


def test_lines_page_carries_the_revision() -> None:
    page = LinesPage(1, 0, 10, CHAPTER.lines, REVISION)

    assert page.revision == REVISION
    assert page != attr.evolve(page, revision=LEGACY_REVISION)
