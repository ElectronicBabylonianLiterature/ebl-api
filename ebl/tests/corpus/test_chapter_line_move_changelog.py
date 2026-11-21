import json
from typing import Callable

import dictdiffer
import pytest
from freezegun import freeze_time
from pymongo.database import Database

from ebl.changelog import create_entry, is_storable
from ebl.corpus.application.chapter_changelog import (
    create_chapter_diff,
    create_line_move_diff,
    dump_chapter_document,
)
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.corpus import COLLECTION
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line_move import LineMove
from ebl.tests.corpus.line_move_support import (
    LONG_LINE_COUNT,
    LONG_MOVE,
    MOVE,
    MOVES,
    SHORT_MOVE,
    create_move_chapter,
    find_diff_size,
    invert,
    move_chapter_line,
)
from ebl.tests.corpus.lines_edit_support import find_chapter_changelog_entries
from ebl.tests.corpus.outline_support import remove_key
from ebl.tests.corpus.support import ANY_USER


@pytest.fixture
def long_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_move_chapter(LONG_LINE_COUNT))


@pytest.mark.parametrize("move", MOVES)
def test_changelog_entry_of_a_move_replays_the_move(
    database: Database, writer: ChapterEditWriter, move_chapter: Chapter, move: LineMove
) -> None:
    old_document = dump_chapter_document(writer.find_chapter(move_chapter.id_))

    saved = writer.move_line(move_chapter.id_, move, LEGACY_REVISION, ANY_USER)
    (entry,) = find_chapter_changelog_entries(database)

    assert dictdiffer.patch(entry["diff"], old_document) == dump_chapter_document(
        saved.chapter
    )
    assert saved.chapter == move_chapter_line(move_chapter, move)


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog_entry_of_a_move_is_the_entry_of_the_line_move_diff(
    database: Database, writer: ChapterEditWriter, move_chapter: Chapter
) -> None:
    expected = create_entry(
        ANY_USER.profile,
        COLLECTION,
        move_chapter.id_.to_tuple(),
        create_line_move_diff(
            MOVE, move_chapter, move_chapter_line(move_chapter, MOVE)
        ),
    )

    writer.move_line(move_chapter.id_, MOVE, LEGACY_REVISION, ANY_USER)
    (entry,) = find_chapter_changelog_entries(database)

    assert remove_key(entry, "_id") == json.loads(json.dumps(expected))


def test_changelog_entry_of_a_long_move_is_as_small_as_of_a_short_move(
    database: Database, writer: ChapterEditWriter, long_chapter: Chapter
) -> None:
    short = writer.move_line(long_chapter.id_, SHORT_MOVE, LEGACY_REVISION, ANY_USER)
    restored = writer.move_line(
        long_chapter.id_, invert(SHORT_MOVE), short.revision, ANY_USER
    )

    long = writer.move_line(long_chapter.id_, LONG_MOVE, restored.revision, ANY_USER)
    short_entry, _, long_entry = find_chapter_changelog_entries(database)

    assert long.chapter == move_chapter_line(long_chapter, LONG_MOVE)
    assert find_diff_size(long_entry["diff"]) == find_diff_size(short_entry["diff"])


def test_long_move_is_recorded_where_the_entry_of_the_chapter_diff_does_not_fit(
    database: Database,
    writer: ChapterEditWriter,
    long_chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    moved_chapter = move_chapter_line(long_chapter, LONG_MOVE)
    chapter_entry = create_entry(
        ANY_USER.profile,
        COLLECTION,
        long_chapter.id_.to_tuple(),
        create_chapter_diff(long_chapter, moved_chapter),
    )
    monkeypatch.setattr(
        "ebl.changelog.MAX_BSON_SIZE", find_diff_size(chapter_entry["diff"]) // 10
    )

    saved = writer.move_line(long_chapter.id_, LONG_MOVE, LEGACY_REVISION, ANY_USER)

    assert not is_storable(chapter_entry)
    assert saved.chapter == moved_chapter
    assert len(find_chapter_changelog_entries(database)) == 1
