from typing import Callable

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import ChapterEditKind, post_edit
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)
from ebl.tests.corpus.outline_support import create_outline_chapter, dump_outline

VIEW_PREFIXES = ("view=outline&", "")
INVALID_REVISION_QUERIES = ("revision=", "revision=a&revision=b")


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


def test_saving_at_the_current_revision_returns_the_new_revision(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    edit = edit_kind.create_edit(chapter, 0)

    result = post_edit(client, chapter, edit, "view=outline&revision=legacy")
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == edit.update_outline(dump_outline(chapter, revision))
    assert revision != LEGACY_REVISION
    assert count_chapter_changelog_entries(database) == 1


def test_saving_with_the_revision_of_the_previous_save(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    first_edit = edit_kind.create_edit(chapter, 0)
    second_edit = edit_kind.create_edit(chapter, 1)
    first_result = post_edit(client, chapter, first_edit, "view=outline")
    first_revision = read_json(first_result)["revision"]

    second_result = post_edit(
        client, chapter, second_edit, f"view=outline&revision={first_revision}"
    )
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert second_result.status == falcon.HTTP_OK
    assert second_result.json == second_edit.update_outline(
        first_edit.update_outline(dump_outline(chapter, revision))
    )
    assert revision != first_revision
    assert count_chapter_changelog_entries(database) == 2


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_second_save_at_the_same_revision_conflicts(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    view: str,
) -> None:
    query_string = f"{view}revision=legacy"

    first_result = post_edit(
        client, chapter, edit_kind.create_edit(chapter, 0), query_string
    )
    stored_chapter = find_stored_chapter(database, chapter)
    second_result = post_edit(
        client, chapter, edit_kind.create_edit(chapter, 1), query_string
    )

    assert first_result.status == falcon.HTTP_OK
    assert second_result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_saving_at_a_stale_revision(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    view: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    conflict = chapter_revision_conflict(chapter.id_, STALE_REVISION, LEGACY_REVISION)

    result = post_edit(
        client,
        chapter,
        edit_kind.create_edit(chapter, 0),
        f"{view}revision={STALE_REVISION}",
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert read_json(result)["description"] == str(conflict)
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_saving_an_updated_chapter_at_the_legacy_revision(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    text_repository.update(chapter.id_, chapter)
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_edit(
        client, chapter, edit_kind.create_edit(chapter, 0), "revision=legacy"
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("query_string", INVALID_REVISION_QUERIES)
def test_saving_with_an_invalid_revision(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    query_string: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_edit(
        client,
        chapter,
        edit_kind.create_edit(chapter, 0),
        f"view=outline&{query_string}",
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0
