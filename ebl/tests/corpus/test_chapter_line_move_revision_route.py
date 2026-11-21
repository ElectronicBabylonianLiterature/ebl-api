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
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.line_move_support import (
    MOVE,
    MOVE_QUERY,
    post_move,
)
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)

VIEW_PREFIXES = ("view=outline&", "")


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_stale_revision_conflicts_and_the_fresh_revision_succeeds(
    client: testing.TestClient, database: Database, move_chapter: Chapter, view: str
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    conflict = chapter_revision_conflict(
        move_chapter.id_, STALE_REVISION, LEGACY_REVISION
    )

    stale_result = post_move(
        client, move_chapter, MOVE, f"{view}revision={STALE_REVISION}"
    )
    chapter_after_conflict = find_stored_chapter(database, move_chapter)
    changelog_entries_after_conflict = count_chapter_changelog_entries(database)
    fresh_result = post_move(client, move_chapter, MOVE, f"{view}revision=legacy")

    assert stale_result.status == falcon.HTTP_CONFLICT
    assert read_json(stale_result)["description"] == str(conflict)
    assert chapter_after_conflict == stored_chapter
    assert changelog_entries_after_conflict == 0
    assert fresh_result.status == falcon.HTTP_OK
    assert find_stored_chapter(database, move_chapter) != stored_chapter
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_second_move_at_the_same_revision_conflicts(
    client: testing.TestClient, database: Database, move_chapter: Chapter, view: str
) -> None:
    query_string = f"{view}revision=legacy"

    first_result = post_move(client, move_chapter, MOVE, query_string)
    stored_chapter = find_stored_chapter(database, move_chapter)
    second_result = post_move(client, move_chapter, LineMove(3, 1), query_string)

    assert first_result.status == falcon.HTTP_OK
    assert second_result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 1


def test_moving_in_an_updated_chapter_at_the_legacy_revision(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
) -> None:
    text_repository.update(move_chapter.id_, move_chapter)
    stored_chapter = find_stored_chapter(database, move_chapter)

    result = post_move(client, move_chapter, MOVE, MOVE_QUERY)

    assert result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_stale_revision_is_reported_before_an_invalid_move(
    client: testing.TestClient, move_chapter: Chapter
) -> None:
    result = post_move(client, move_chapter, LineMove(4, 0), "revision=stale")

    assert result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("revision", [LEGACY_REVISION, STALE_REVISION])
def test_moving_in_an_unknown_chapter(
    client: testing.TestClient, database: Database, move_chapter: Chapter, revision: str
) -> None:
    missing_chapter = attr.evolve(move_chapter, name=f"{move_chapter.name} missing")
    stored_chapter = find_stored_chapter(database, move_chapter)

    result = post_move(
        client, missing_chapter, MOVE, f"view=outline&revision={revision}"
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("query_string", ["", MOVE_QUERY, "revision=legacy"])
def test_moving_requires_write_scope(
    guest_client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    query_string: str,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)

    result = post_move(guest_client, move_chapter, MOVE, query_string)

    assert result.status == falcon.HTTP_FORBIDDEN
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0
