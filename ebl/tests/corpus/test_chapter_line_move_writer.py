import re

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.errors import ConflictError, DataError, NotFoundError
from ebl.tests.corpus.line_move_support import (
    MOVE,
    MOVES,
    assert_lines_are_annotated,
    invert,
    move_chapter_line,
)
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
)
from ebl.tests.corpus.revision_save_support import update_after_read
from ebl.tests.corpus.support import ANY_USER

INVALID_MOVES = (LineMove(4, 0), LineMove(0, 4), LineMove(1, 1))
EXTENT_BREAKING_MOVES = (LineMove(0, 1), LineMove(2, 1))


@pytest.mark.parametrize("move", MOVES)
def test_move_line_returns_and_stores_the_moved_chapter(
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
    move: LineMove,
) -> None:
    expected = move_chapter_line(move_chapter, move)

    saved = writer.move_line(move_chapter.id_, move, LEGACY_REVISION, ANY_USER)

    assert saved.chapter == expected
    assert saved.revision == text_repository.find_chapter_revision(move_chapter.id_)
    assert saved.revision != LEGACY_REVISION
    assert writer.find_chapter(move_chapter.id_) == expected
    assert_lines_are_annotated(text_repository.find_chapter(move_chapter.id_).lines)


def test_move_line_writes_one_changelog_entry(
    database: Database, writer: ChapterEditWriter, move_chapter: Chapter
) -> None:
    writer.move_line(move_chapter.id_, MOVE, LEGACY_REVISION, ANY_USER)

    assert count_chapter_changelog_entries(database) == 1


def test_move_line_at_the_revision_of_the_previous_move(
    database: Database, writer: ChapterEditWriter, move_chapter: Chapter
) -> None:
    first = writer.move_line(move_chapter.id_, MOVE, LEGACY_REVISION, ANY_USER)

    second = writer.move_line(move_chapter.id_, invert(MOVE), first.revision, ANY_USER)

    assert second.revision != first.revision
    assert second.chapter == move_chapter
    assert writer.find_chapter(move_chapter.id_) == move_chapter
    assert count_chapter_changelog_entries(database) == 2


def test_move_line_at_stale_revision(
    database: Database, writer: ChapterEditWriter, move_chapter: Chapter
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    conflict = chapter_revision_conflict(
        move_chapter.id_, STALE_REVISION, LEGACY_REVISION
    )

    with pytest.raises(ConflictError, match=re.escape(str(conflict))):
        writer.move_line(move_chapter.id_, MOVE, STALE_REVISION, ANY_USER)

    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_move_line_does_not_overwrite_a_concurrent_update(
    database: Database,
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
) -> None:
    with pytest.MonkeyPatch.context() as patch:
        update_after_read(patch, text_repository, move_chapter)
        with pytest.raises(ConflictError, match="expected revision legacy"):
            writer.move_line(move_chapter.id_, MOVE, LEGACY_REVISION, ANY_USER)

    assert text_repository.find_chapter_revision(move_chapter.id_) != LEGACY_REVISION
    assert writer.find_chapter(move_chapter.id_) == move_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("move", INVALID_MOVES)
def test_move_line_with_an_invalid_move(
    database: Database,
    writer: ChapterEditWriter,
    move_chapter: Chapter,
    move: LineMove,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)

    with pytest.raises(DataError, match="Invalid line move: "):
        writer.move_line(move_chapter.id_, move, LEGACY_REVISION, ANY_USER)

    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("move", EXTENT_BREAKING_MOVES)
def test_move_line_breaking_a_translation_extent(
    database: Database,
    writer: ChapterEditWriter,
    extent_chapter: Chapter,
    move: LineMove,
) -> None:
    stored_chapter = find_stored_chapter(database, extent_chapter)

    with pytest.raises(DataError, match="extent"):
        writer.move_line(extent_chapter.id_, move, LEGACY_REVISION, ANY_USER)

    assert find_stored_chapter(database, extent_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_stale_revision_is_reported_before_an_invalid_move(
    writer: ChapterEditWriter, move_chapter: Chapter
) -> None:
    with pytest.raises(ConflictError):
        writer.move_line(move_chapter.id_, INVALID_MOVES[0], STALE_REVISION, ANY_USER)


@pytest.mark.parametrize("revision", [LEGACY_REVISION, STALE_REVISION])
def test_move_line_of_an_unknown_chapter(
    database: Database,
    writer: ChapterEditWriter,
    move_chapter: Chapter,
    revision: str,
) -> None:
    missing_id = attr.evolve(move_chapter.id_, name=f"{move_chapter.name} missing")

    with pytest.raises(NotFoundError, match=re.escape(f"Chapter {missing_id}")):
        writer.move_line(missing_id, MOVE, revision, ANY_USER)

    assert count_chapter_changelog_entries(database) == 0
