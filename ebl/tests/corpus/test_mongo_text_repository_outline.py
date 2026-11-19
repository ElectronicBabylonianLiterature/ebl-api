import re
from functools import partial
from typing import Callable, Sequence

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.lines_pagination import MAX_LINES_OFFSET
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.lines_page import LinesPage
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_outline import (
    aggregate_chapter_outline,
    aggregate_lines_page,
)
from ebl.errors import NotFoundError
from ebl.tests.corpus.outline_support import (
    create_chapter_with_lines,
    create_outline_chapter,
    create_outline_document,
)
from ebl.tests.factories.corpus import ChapterFactory
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION

LINE_COUNT = 12
OMITTED_CHAPTER_KEYS: Sequence[str] = ("_id", "signs", "record", "parserVersion")
OMITTED_MANUSCRIPT_KEYS: Sequence[str] = ("colophon", "unplacedLines", "oldSigla")
OMITTED_LINE_KEYS: Sequence[str] = ("oldLineNumbers", "intertext", "manuscriptId")
OMITTED_MANUSCRIPT_LINE_KEYS: Sequence[str] = ("line", "paratext", "omittedWords")
OMITTED_KEYS: Sequence[str] = (
    *OMITTED_CHAPTER_KEYS,
    *OMITTED_MANUSCRIPT_KEYS,
    *OMITTED_LINE_KEYS,
    *OMITTED_MANUSCRIPT_LINE_KEYS,
)


def create_empty_chapter() -> Chapter:
    return ChapterFactory.build(manuscripts=(), lines=(), uncertain_fragments=())


def create_sibling_chapter(chapter: Chapter) -> Chapter:
    return attr.evolve(chapter, name=f"{chapter.name} sibling", lines=chapter.lines[1:])


def remove_optional_fields(chapter: Chapter) -> Chapter:
    return attr.evolve(
        chapter,
        uncertain_fragments=(),
        lines=tuple(
            attr.evolve(
                line,
                translation=(),
                variants=tuple(
                    attr.evolve(variant, parallel_lines=()) for variant in line.variants
                ),
            )
            for line in chapter.lines
        ),
    )


@pytest.fixture
def long_chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_chapter_with_lines(LINE_COUNT)
    text_repository.create_chapter(chapter)
    return chapter


@pytest.fixture
def outline_chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_outline_chapter()
    text_repository.create_chapter(chapter)
    return chapter


@pytest.mark.parametrize(
    "create_chapter",
    [
        create_outline_chapter,
        partial(create_chapter_with_lines, LINE_COUNT),
        create_empty_chapter,
        ChapterFactory.build,
    ],
)
def test_find_chapter_outline(
    text_repository: MongoTextRepository, create_chapter: Callable[[], Chapter]
) -> None:
    chapter = create_chapter()
    text_repository.create_chapter(chapter)

    outline = text_repository.find_chapter_outline(chapter.id_)

    assert outline == ChapterOutline.of_chapter(chapter)


def test_find_chapter_outline_of_document_without_optional_fields(
    database: Database, text_repository: MongoTextRepository
) -> None:
    chapter = create_outline_chapter()
    document = stored_dump(ChapterSchema(), chapter)
    del document["uncertainFragments"]
    for line in document["lines"]:
        del line["translation"]
        for variant in line["variants"]:
            del variant["parallelLines"]
    database[CHAPTERS_COLLECTION].insert_one(document)

    outline = text_repository.find_chapter_outline(chapter.id_)

    assert outline == ChapterOutline.of_chapter(remove_optional_fields(chapter))


def test_chapter_outline_aggregation_projects_the_outline_document(
    database: Database, outline_chapter: Chapter
) -> None:
    pipeline = aggregate_chapter_outline(outline_chapter.id_)

    documents = list(database[CHAPTERS_COLLECTION].aggregate(pipeline))

    assert documents == [create_outline_document(outline_chapter)]


def test_chapter_outline_aggregation_omits_fields_the_outline_does_not_need(
    database: Database, outline_chapter: Chapter
) -> None:
    chapters = database[CHAPTERS_COLLECTION]
    stored_chapter = chapters.find_one({"name": outline_chapter.name})

    document = next(chapters.aggregate(aggregate_chapter_outline(outline_chapter.id_)))

    assert [key for key in OMITTED_KEYS if not has_key(stored_chapter, key)] == []
    assert [key for key in OMITTED_KEYS if has_key(document, key)] == []


@pytest.mark.parametrize(
    "offset,limit",
    [(0, 10), (0, 1), (3, 4), (0, 12), (5, 50), (10, 10), (11, 1), (11, 50)],
)
def test_find_lines_page(
    text_repository: MongoTextRepository, long_chapter: Chapter, offset: int, limit: int
) -> None:
    expected_lines = long_chapter.lines[offset:][:limit]

    page = text_repository.find_lines_page(long_chapter.id_, offset, limit)

    assert len(expected_lines) > 0
    assert page == LinesPage(LINE_COUNT, offset, limit, expected_lines)


@pytest.mark.parametrize("offset", [LINE_COUNT, LINE_COUNT + 1, MAX_LINES_OFFSET])
def test_find_lines_page_past_the_end(
    text_repository: MongoTextRepository, long_chapter: Chapter, offset: int
) -> None:
    page = text_repository.find_lines_page(long_chapter.id_, offset, 50)

    assert page == LinesPage(LINE_COUNT, offset, 50, ())


def test_find_lines_page_of_chapter_without_lines(
    text_repository: MongoTextRepository,
) -> None:
    chapter = create_empty_chapter()
    text_repository.create_chapter(chapter)

    page = text_repository.find_lines_page(chapter.id_, 0, 10)

    assert page == LinesPage(0, 0, 10, ())


def test_lines_page_aggregation_returns_total_and_slice(
    database: Database, long_chapter: Chapter
) -> None:
    pipeline = aggregate_lines_page(long_chapter.id_, 2, 3)
    stored_lines = stored_dump(ChapterSchema(), long_chapter)["lines"]

    documents = list(database[CHAPTERS_COLLECTION].aggregate(pipeline))

    assert documents == [{"total": LINE_COUNT, "lines": stored_lines[2:5]}]


def test_finding_selects_chapter_by_id(
    text_repository: MongoTextRepository, outline_chapter: Chapter
) -> None:
    sibling = create_sibling_chapter(outline_chapter)
    text_repository.create_chapter(sibling)

    for chapter in (outline_chapter, sibling):
        outline = text_repository.find_chapter_outline(chapter.id_)
        page = text_repository.find_lines_page(chapter.id_, 0, 50)

        assert outline == ChapterOutline.of_chapter(chapter)
        assert page == LinesPage(len(chapter.lines), 0, 50, chapter.lines)


@pytest.mark.parametrize(
    "find",
    [
        lambda repository, id_: repository.find_chapter_outline(id_),
        lambda repository, id_: repository.find_lines_page(id_, 0, 10),
    ],
)
def test_chapter_not_found(
    text_repository: MongoTextRepository,
    long_chapter: Chapter,
    find: Callable[[MongoTextRepository, ChapterId], object],
) -> None:
    missing_id = attr.evolve(long_chapter.id_, name=f"{long_chapter.name} missing")

    with pytest.raises(
        NotFoundError, match=re.escape(f"Chapter {missing_id} not found.")
    ):
        find(text_repository, missing_id)


@pytest.mark.parametrize(
    "offset,limit,message",
    [
        (-1, 10, "offset must be between 0 and 2147483647, got -1 instead"),
        (2**31, 10, "offset must be between 0 and 2147483647, got 2147483648 instead"),
        (0, 0, "limit must be at least 1, got 0 instead"),
        (0, -1, "limit must be at least 1, got -1 instead"),
    ],
)
def test_find_lines_page_rejects_invalid_slice(
    text_repository: MongoTextRepository,
    long_chapter: Chapter,
    offset: int,
    limit: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        text_repository.find_lines_page(long_chapter.id_, offset, limit)
