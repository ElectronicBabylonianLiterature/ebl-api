import dictdiffer
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.chapter_changelog import dump_chapter_document
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_move_support import MOVE_QUERY
from ebl.tests.corpus.lines_edit_support import find_chapter_changelog_entries
from ebl.tests.corpus.revision_save_support import (
    SAVE_IDS,
    SAVES_AT_REVISION,
    RequestFactory,
)


@pytest.mark.parametrize("create_request", SAVES_AT_REVISION, ids=SAVE_IDS)
def test_changelog_entry_of_a_save_at_a_revision_replays_the_save(
    client: testing.TestClient,
    database: Database,
    writer: ChapterEditWriter,
    move_chapter: Chapter,
    create_request: RequestFactory,
) -> None:
    old_document = dump_chapter_document(writer.find_chapter(move_chapter.id_))

    result = post_edit(client, move_chapter, create_request(move_chapter), MOVE_QUERY)
    (entry,) = find_chapter_changelog_entries(database)
    new_document = dump_chapter_document(writer.find_chapter(move_chapter.id_))

    assert result.status == falcon.HTTP_OK
    assert new_document != old_document
    assert dictdiffer.patch(entry["diff"], old_document) == new_document
