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
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_move_support import MOVE_QUERY
from ebl.tests.corpus.lines_edit_support import (
    OTHER_EDITED_NUMBER,
    count_chapter_changelog_entries,
    create_body,
    find_stored_chapter,
    post_lines,
    read_json,
    update_chapter,
)
from ebl.tests.corpus.revision_save_support import (
    SAVE_IDS,
    SAVES_AT_REVISION,
    RequestFactory,
    read_from_lagging_member,
)

NEWER_EDIT_INDEX = 0


def save_newer_edit(client: testing.TestClient, chapter: Chapter) -> str:
    edited_chapter = update_chapter(chapter, NEWER_EDIT_INDEX, OTHER_EDITED_NUMBER)
    result = post_lines(
        client, chapter, create_body(edited_chapter, NEWER_EDIT_INDEX), MOVE_QUERY
    )
    assert result.status == falcon.HTTP_OK
    return read_json(result)["revision"]


@pytest.mark.parametrize("create_request", SAVES_AT_REVISION, ids=SAVE_IDS)
def test_save_computed_from_a_lagging_read_is_refused_and_can_be_repeated(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
    create_request: RequestFactory,
) -> None:
    lagging_read = text_repository.find_chapter_with_revision(move_chapter.id_)
    fresh_revision = save_newer_edit(client, move_chapter)
    stored_chapter = find_stored_chapter(database, move_chapter)
    request = create_request(move_chapter)
    query_string = f"view=outline&revision={fresh_revision}"
    conflict = chapter_revision_conflict(
        move_chapter.id_, fresh_revision, LEGACY_REVISION
    )

    with pytest.MonkeyPatch.context() as patch:
        read_from_lagging_member(patch, text_repository, lagging_read)
        refused_result = post_edit(client, move_chapter, request, query_string)
    chapter_after_refusal = find_stored_chapter(database, move_chapter)
    changelog_entries_after_refusal = count_chapter_changelog_entries(database)
    newer_line = text_repository.find_chapter(move_chapter.id_).lines[NEWER_EDIT_INDEX]
    repeated_result = post_edit(client, move_chapter, request, query_string)

    assert refused_result.status == falcon.HTTP_CONFLICT
    assert read_json(refused_result)["description"] == str(conflict)
    assert chapter_after_refusal == stored_chapter
    assert newer_line.number == OTHER_EDITED_NUMBER
    assert newer_line != lagging_read[0].lines[NEWER_EDIT_INDEX]
    assert changelog_entries_after_refusal == 1
    assert repeated_result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 2
