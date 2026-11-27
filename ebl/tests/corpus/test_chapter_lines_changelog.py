from typing import Callable

import dictdiffer
import pytest
from pymongo.database import Database

from ebl.changelog import create_entry, is_storable
from ebl.corpus.application.chapter_changelog import (
    create_chapter_diff,
    dump_chapter_document,
)
from ebl.corpus.application.chapter_changes import change_lines
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.corpus import COLLECTION
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.tests.corpus.line_move_support import (
    LONG_LINE_COUNT,
    create_move_chapter,
    find_diff_size,
)
from ebl.tests.corpus.lines_edit_support import find_chapter_changelog_entries
from ebl.tests.corpus.support import ANY_USER
from ebl.transliteration.application.sign_repository import SignRepository

LAST_INDEX_AFTER_DELETE = LONG_LINE_COUNT - 2
DELETE_FIRST = LinesUpdate([], {0}, {})
DELETE_LAST = LinesUpdate([], {LAST_INDEX_AFTER_DELETE}, {})


@pytest.fixture
def long_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_move_chapter(LONG_LINE_COUNT))


def test_entry_of_a_delete_at_the_start_is_as_small_as_at_the_end(
    database: Database, writer: ChapterEditWriter, long_chapter: Chapter
) -> None:
    first = writer.save_lines(long_chapter.id_, DELETE_FIRST, LEGACY_REVISION, ANY_USER)
    last = writer.save_lines(long_chapter.id_, DELETE_LAST, first.revision, ANY_USER)
    first_size, last_size = (
        find_diff_size(entry["diff"])
        for entry in find_chapter_changelog_entries(database)
    )

    assert last.chapter.lines == long_chapter.lines[1:-1]
    assert abs(first_size - last_size) < last_size / 10
    assert (
        find_diff_size(create_chapter_diff(long_chapter, first.chapter))
        > 10 * first_size
    )


def test_delete_at_the_start_is_recorded_where_the_entry_of_the_chapter_diff_does_not_fit(
    database: Database,
    writer: ChapterEditWriter,
    registered_sign_repository: SignRepository,
    long_chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_chapter = writer.find_chapter(long_chapter.id_)
    shortened_chapter = change_lines(
        DELETE_FIRST, registered_sign_repository, old_chapter
    ).new
    chapter_entry = create_entry(
        ANY_USER.profile,
        COLLECTION,
        long_chapter.id_.to_tuple(),
        create_chapter_diff(old_chapter, shortened_chapter),
    )
    monkeypatch.setattr(
        "ebl.changelog.MAX_BSON_SIZE", find_diff_size(chapter_entry["diff"]) // 10
    )

    saved = writer.save_lines(long_chapter.id_, DELETE_FIRST, LEGACY_REVISION, ANY_USER)
    (entry,) = find_chapter_changelog_entries(database)

    assert not is_storable(chapter_entry)
    assert saved.chapter == shortened_chapter
    assert dictdiffer.patch(
        entry["diff"], dump_chapter_document(old_chapter)
    ) == dump_chapter_document(shortened_chapter)
