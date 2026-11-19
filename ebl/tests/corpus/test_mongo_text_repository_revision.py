import re
from typing import Callable, Mapping

import attr
import pytest
from bson import ObjectId
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.domain.lines_page import LinesPage
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    REVISION_FIELD,
    revision_query,
)
from ebl.errors import ConflictError, NotFoundError
from ebl.tests.corpus.lines_edit_support import STALE_REVISION, find_stored_chapter
from ebl.tests.corpus.outline_support import create_chapter_with_lines

LINE_COUNT = 4


def remove_first_line(chapter: Chapter) -> Chapter:
    return attr.evolve(chapter, lines=chapter.lines[1:])


def create_missing_id(chapter: Chapter) -> ChapterId:
    return attr.evolve(chapter.id_, name=f"{chapter.name} missing")


@pytest.fixture
def chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_chapter_with_lines(LINE_COUNT)
    text_repository.create_chapter(chapter)
    return chapter


@pytest.fixture
def updated_chapter(text_repository: MongoTextRepository, chapter: Chapter) -> Chapter:
    updated_chapter = remove_first_line(chapter)
    text_repository.update(chapter.id_, updated_chapter)
    return updated_chapter


def test_revision_field() -> None:
    assert REVISION_FIELD == "_cacheRevision"


@pytest.mark.parametrize(
    "revision,expected",
    [
        (LEGACY_REVISION, {"_cacheRevision": None}),
        (STALE_REVISION, {"_cacheRevision": STALE_REVISION}),
    ],
)
def test_revision_query(revision: str, expected: Mapping[str, object]) -> None:
    assert revision_query(revision) == expected


def test_created_chapter_has_the_legacy_revision(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    assert REVISION_FIELD not in find_stored_chapter(database, chapter)
    assert text_repository.find_chapter_revision(chapter.id_) == LEGACY_REVISION


def test_find_chapter_revision_after_update(
    database: Database, text_repository: MongoTextRepository, updated_chapter: Chapter
) -> None:
    revision = text_repository.find_chapter_revision(updated_chapter.id_)

    assert revision == find_stored_chapter(database, updated_chapter)[REVISION_FIELD]
    assert ObjectId.is_valid(revision)


def test_every_update_writes_a_new_revision(
    text_repository: MongoTextRepository, updated_chapter: Chapter
) -> None:
    first_revision = text_repository.find_chapter_revision(updated_chapter.id_)

    text_repository.update(updated_chapter.id_, updated_chapter)

    assert text_repository.find_chapter_revision(updated_chapter.id_) not in (
        first_revision,
        LEGACY_REVISION,
    )


def test_update_at_legacy_revision(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    updated_chapter = remove_first_line(chapter)

    revision = text_repository.update_at_revision(
        chapter.id_, updated_chapter, LEGACY_REVISION
    )

    assert revision == find_stored_chapter(database, chapter)[REVISION_FIELD]
    assert revision == text_repository.find_chapter_revision(chapter.id_)
    assert revision != LEGACY_REVISION
    assert text_repository.find_chapter(chapter.id_).lines == updated_chapter.lines


def test_update_at_stored_revision(
    database: Database, text_repository: MongoTextRepository, updated_chapter: Chapter
) -> None:
    old_revision = text_repository.find_chapter_revision(updated_chapter.id_)
    next_chapter = remove_first_line(updated_chapter)

    revision = text_repository.update_at_revision(
        updated_chapter.id_, next_chapter, old_revision
    )

    assert revision == find_stored_chapter(database, updated_chapter)[REVISION_FIELD]
    assert revision not in (old_revision, LEGACY_REVISION)
    assert text_repository.find_chapter(next_chapter.id_).lines == next_chapter.lines


def test_update_at_the_revision_returned_by_the_previous_update(
    text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    first_chapter = remove_first_line(chapter)
    second_chapter = remove_first_line(first_chapter)
    first_revision = text_repository.update_at_revision(
        chapter.id_, first_chapter, LEGACY_REVISION
    )

    second_revision = text_repository.update_at_revision(
        chapter.id_, second_chapter, first_revision
    )

    assert second_revision == text_repository.find_chapter_revision(chapter.id_)
    assert second_revision != first_revision
    assert text_repository.find_chapter(chapter.id_).lines == second_chapter.lines


@pytest.mark.parametrize("stale_revision", [STALE_REVISION, LEGACY_REVISION])
def test_update_at_stale_revision(
    database: Database,
    text_repository: MongoTextRepository,
    updated_chapter: Chapter,
    stale_revision: str,
) -> None:
    stored_chapter = find_stored_chapter(database, updated_chapter)
    conflict = chapter_revision_conflict(
        updated_chapter.id_, stale_revision, stored_chapter[REVISION_FIELD]
    )

    with pytest.raises(ConflictError, match=re.escape(str(conflict))):
        text_repository.update_at_revision(
            updated_chapter.id_, remove_first_line(updated_chapter), stale_revision
        )

    assert find_stored_chapter(database, updated_chapter) == stored_chapter


def test_update_of_never_updated_chapter_at_stale_revision(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    conflict = chapter_revision_conflict(chapter.id_, STALE_REVISION, LEGACY_REVISION)

    with pytest.raises(ConflictError, match=re.escape(str(conflict))):
        text_repository.update_at_revision(
            chapter.id_, remove_first_line(chapter), STALE_REVISION
        )

    assert find_stored_chapter(database, chapter) == stored_chapter


def test_only_the_first_update_at_a_revision_succeeds(
    text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    first_chapter = remove_first_line(chapter)
    first_revision = text_repository.update_at_revision(
        chapter.id_, first_chapter, LEGACY_REVISION
    )

    with pytest.raises(ConflictError):
        text_repository.update_at_revision(
            chapter.id_, remove_first_line(first_chapter), LEGACY_REVISION
        )

    assert text_repository.find_chapter_revision(chapter.id_) == first_revision
    assert text_repository.find_chapter(chapter.id_).lines == first_chapter.lines


def test_update_at_revision_changes_only_the_selected_chapter(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    sibling = attr.evolve(chapter, name=f"{chapter.name} sibling")
    text_repository.create_chapter(sibling)
    stored_sibling = find_stored_chapter(database, sibling)

    text_repository.update_at_revision(
        chapter.id_, remove_first_line(chapter), LEGACY_REVISION
    )

    assert find_stored_chapter(database, sibling) == stored_sibling
    assert text_repository.find_chapter_revision(sibling.id_) == LEGACY_REVISION


@pytest.mark.parametrize(
    "use_revision",
    [
        lambda repository, chapter: repository.find_chapter_revision(
            create_missing_id(chapter)
        ),
        lambda repository, chapter: repository.update_at_revision(
            create_missing_id(chapter), chapter, LEGACY_REVISION
        ),
        lambda repository, chapter: repository.update_at_revision(
            create_missing_id(chapter), chapter, STALE_REVISION
        ),
    ],
)
def test_revision_of_unknown_chapter(
    text_repository: MongoTextRepository,
    chapter: Chapter,
    use_revision: Callable[[MongoTextRepository, Chapter], object],
) -> None:
    message = f"Chapter {create_missing_id(chapter)} not found."

    with pytest.raises(NotFoundError, match=re.escape(message)):
        use_revision(text_repository, chapter)


def test_outline_and_lines_page_carry_the_revision(
    text_repository: MongoTextRepository, updated_chapter: Chapter
) -> None:
    revision = text_repository.find_chapter_revision(updated_chapter.id_)

    outline = text_repository.find_chapter_outline(updated_chapter.id_)
    page = text_repository.find_lines_page(updated_chapter.id_, 1, 2)

    assert outline == ChapterOutline.of_chapter(updated_chapter, revision)
    assert page == LinesPage(LINE_COUNT - 1, 1, 2, updated_chapter.lines[1:3], revision)
    assert revision != LEGACY_REVISION
