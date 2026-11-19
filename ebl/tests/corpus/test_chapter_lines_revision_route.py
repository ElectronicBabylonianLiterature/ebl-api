from typing import Callable

import attr
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
from ebl.tests.corpus.lines_edit_support import (
    EDITED_INDEX,
    OTHER_EDITED_NUMBER,
    STALE_REVISION,
    count_chapter_changelog_entries,
    create_body,
    find_stored_chapter,
    post_lines,
    read_json,
    update_chapter,
)
from ebl.tests.corpus.outline_support import create_outline_chapter, dump_outline
from ebl.tests.corpus.support import create_chapter_dto
from ebl.tests.factories.corpus import ChapterFactory

INVALID_REVISION_QUERIES = ("revision=", "revision=a&revision=b")


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


@pytest.fixture
def updated_chapter(chapter: Chapter) -> Chapter:
    return update_chapter(chapter, EDITED_INDEX)


@pytest.fixture
def body(updated_chapter: Chapter) -> str:
    return create_body(updated_chapter, EDITED_INDEX)


def test_saving_the_outline_view_at_the_legacy_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    updated_chapter: Chapter,
    body: str,
) -> None:
    result = post_lines(client, updated_chapter, body, "view=outline&revision=legacy")
    revision = text_repository.find_chapter_revision(updated_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_outline(updated_chapter, revision)
    assert revision != LEGACY_REVISION


@pytest.mark.parametrize(
    "query_string", ["revision=legacy", "view=chapter&revision=legacy"]
)
def test_saving_the_chapter_view_at_the_legacy_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    store_editable_chapter: Callable[[Chapter], Chapter],
    query_string: str,
) -> None:
    chapter = store_editable_chapter(ChapterFactory.build())
    updated_chapter = update_chapter(chapter, 0)

    result = post_lines(client, chapter, create_body(updated_chapter, 0), query_string)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(updated_chapter)
    assert "revision" not in read_json(result)
    assert text_repository.find_chapter(chapter.id_).lines == updated_chapter.lines


@pytest.mark.parametrize("view", ["view=outline&", ""])
def test_saving_at_the_current_revision_writes_one_changelog_entry(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    body: str,
    view: str,
) -> None:
    result = post_lines(client, chapter, body, f"{view}revision=legacy")

    assert result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 1


def test_saving_without_revision_returns_the_stored_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    body: str,
) -> None:
    text_repository.update(chapter.id_, chapter)

    result = post_lines(client, chapter, body, "view=outline")
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_outline(update_chapter(chapter, EDITED_INDEX), revision)


def test_saving_with_the_revision_of_the_previous_save(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    updated_chapter: Chapter,
    body: str,
) -> None:
    next_chapter = update_chapter(updated_chapter, 0, OTHER_EDITED_NUMBER)
    first_result = post_lines(client, updated_chapter, body, "view=outline")
    first_revision = read_json(first_result)["revision"]

    second_result = post_lines(
        client,
        updated_chapter,
        create_body(next_chapter, 0),
        f"view=outline&revision={first_revision}",
    )
    revision = text_repository.find_chapter_revision(updated_chapter.id_)

    assert second_result.status == falcon.HTTP_OK
    assert second_result.json == dump_outline(next_chapter, revision)
    assert revision != first_revision
    assert text_repository.find_chapter(next_chapter.id_).lines == next_chapter.lines


@pytest.mark.parametrize("view", ["view=outline&", ""])
def test_second_save_at_the_same_revision_conflicts(
    client: testing.TestClient,
    database: Database,
    updated_chapter: Chapter,
    body: str,
    view: str,
) -> None:
    query_string = f"{view}revision=legacy"
    other_chapter = update_chapter(updated_chapter, 0, OTHER_EDITED_NUMBER)

    first_result = post_lines(client, updated_chapter, body, query_string)
    stored_chapter = find_stored_chapter(database, updated_chapter)
    second_result = post_lines(
        client, updated_chapter, create_body(other_chapter, 0), query_string
    )

    assert first_result.status == falcon.HTTP_OK
    assert second_result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, updated_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("view", ["view=outline&", ""])
def test_saving_at_a_stale_revision(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    body: str,
    view: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    conflict = chapter_revision_conflict(chapter.id_, STALE_REVISION, LEGACY_REVISION)

    result = post_lines(client, chapter, body, f"{view}revision={STALE_REVISION}")

    assert result.status == falcon.HTTP_CONFLICT
    assert read_json(result)["description"] == str(conflict)
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_saving_an_updated_chapter_at_the_legacy_revision(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    body: str,
) -> None:
    text_repository.update(chapter.id_, chapter)
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_lines(client, chapter, body, "view=outline&revision=legacy")

    assert result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("query_string", INVALID_REVISION_QUERIES)
def test_saving_with_an_invalid_revision(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    body: str,
    query_string: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_lines(client, chapter, body, f"view=outline&{query_string}")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("revision", [LEGACY_REVISION, STALE_REVISION])
def test_saving_an_unknown_chapter_at_a_revision(
    client: testing.TestClient, chapter: Chapter, body: str, revision: str
) -> None:
    missing_chapter = attr.evolve(chapter, name=f"{chapter.name} missing")

    result = post_lines(client, missing_chapter, body, f"revision={revision}")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_saving_at_a_revision_requires_write_scope(
    guest_client: testing.TestClient, database: Database, chapter: Chapter, body: str
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_lines(guest_client, chapter, body, "revision=legacy")

    assert result.status == falcon.HTTP_FORBIDDEN
    assert find_stored_chapter(database, chapter) == stored_chapter
