from typing import List

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.changelog import Changelog
from ebl.corpus.application.chapter_edit_writer import CHANGE_TOO_LARGE
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_move_support import MOVE_QUERY
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)
from ebl.tests.corpus.revision_save_support import (
    SAVE_IDS,
    SAVE_WITHOUT_REVISION_IDS,
    SAVES_AT_REVISION,
    SAVES_WITHOUT_REVISION,
    RequestFactory,
)


@pytest.fixture
def revisions_at_insert(
    changelog: Changelog,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> List[str]:
    revisions: List[str] = []
    insert = changelog.insert

    def record_revision(entry: dict) -> object:
        revisions.append(text_repository.find_chapter_revision(move_chapter.id_))
        return insert(entry)

    monkeypatch.setattr(changelog, "insert", record_revision)
    return revisions


@pytest.mark.parametrize("create_request", SAVES_AT_REVISION, ids=SAVE_IDS)
def test_save_too_large_for_the_changelog_is_refused_and_can_be_repeated(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
    create_request: RequestFactory,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    request = create_request(move_chapter)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("ebl.changelog.MAX_BSON_SIZE", 0)
        refused_result = post_edit(client, move_chapter, request, MOVE_QUERY)
    chapter_after_refusal = find_stored_chapter(database, move_chapter)
    revision_after_refusal = text_repository.find_chapter_revision(move_chapter.id_)
    changelog_entries_after_refusal = count_chapter_changelog_entries(database)
    repeated_result = post_edit(client, move_chapter, request, MOVE_QUERY)

    assert refused_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(refused_result)["description"] == CHANGE_TOO_LARGE
    assert chapter_after_refusal == stored_chapter
    assert revision_after_refusal == LEGACY_REVISION
    assert changelog_entries_after_refusal == 0
    assert repeated_result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("create_request", SAVES_AT_REVISION, ids=SAVE_IDS)
def test_stale_revision_is_reported_before_the_changelog_limit(
    client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    create_request: RequestFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    monkeypatch.setattr("ebl.changelog.MAX_BSON_SIZE", 0)

    result = post_edit(
        client,
        move_chapter,
        create_request(move_chapter),
        f"view=outline&revision={STALE_REVISION}",
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize(
    "create_request", SAVES_WITHOUT_REVISION, ids=SAVE_WITHOUT_REVISION_IDS
)
def test_save_without_revision_is_not_checked_against_the_changelog_limit(
    client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    create_request: RequestFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    monkeypatch.setattr("ebl.changelog.MAX_BSON_SIZE", 0)

    result = post_edit(client, move_chapter, create_request(move_chapter), "")

    assert result.status == falcon.HTTP_OK
    assert find_stored_chapter(database, move_chapter) != stored_chapter
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("create_request", SAVES_AT_REVISION, ids=SAVE_IDS)
def test_changelog_entry_is_inserted_once_after_the_update(
    client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    create_request: RequestFactory,
    revisions_at_insert: List[str],
) -> None:
    result = post_edit(client, move_chapter, create_request(move_chapter), MOVE_QUERY)

    assert result.status == falcon.HTTP_OK
    assert revisions_at_insert == [read_json(result)["revision"]]
    assert count_chapter_changelog_entries(database) == 1
