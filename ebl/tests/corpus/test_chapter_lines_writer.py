import re
from typing import Callable

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.errors import ConflictError, DataError, NotFoundError
from ebl.tests.corpus.lines_edit_support import (
    EDITED_INDEX,
    OTHER_EDITED_NUMBER,
    STALE_REVISION,
    count_chapter_changelog_entries,
    create_lines_update,
    find_stored_chapter,
    update_chapter,
)
from ebl.tests.corpus.outline_support import create_outline_chapter
from ebl.tests.corpus.revision_save_support import update_after_read
from ebl.tests.corpus.support import ANY_USER
from ebl.users.domain.user import User


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


def create_invalid_update(chapter: Chapter) -> LinesUpdate:
    duplicated_line = attr.evolve(
        chapter.lines[0], number=chapter.lines[1].number
    ).set_variant_alignment_flags()
    return LinesUpdate([], set(), {0: duplicated_line})


def test_writer_is_a_corpus(writer: ChapterEditWriter) -> None:
    assert isinstance(writer, Corpus)


@pytest.mark.parametrize("revision", [None, LEGACY_REVISION])
def test_save_lines_of_never_updated_chapter(
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    user: User,
    revision: str,
) -> None:
    updated_chapter = update_chapter(chapter, EDITED_INDEX)
    lines = create_lines_update(updated_chapter, EDITED_INDEX)

    saved = writer.save_lines(chapter.id_, lines, revision, user)

    assert saved.chapter.lines == updated_chapter.lines
    assert saved.revision == text_repository.find_chapter_revision(chapter.id_)
    assert saved.revision != LEGACY_REVISION
    assert text_repository.find_chapter(chapter.id_).lines == updated_chapter.lines


def test_save_lines_returns_the_chapter_update_lines_returns(
    writer: ChapterEditWriter,
    corpus: Corpus,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    user: User,
) -> None:
    sibling = attr.evolve(chapter, name=f"{chapter.name} sibling")
    text_repository.create_chapter(sibling)
    updated_chapter = update_chapter(chapter, EDITED_INDEX)
    lines = create_lines_update(updated_chapter, EDITED_INDEX)
    expected = attr.evolve(
        corpus.update_lines(sibling.id_, lines, user), name=chapter.name
    )

    saved = writer.save_lines(chapter.id_, lines, None, user)
    saved_again = writer.save_lines(chapter.id_, lines, saved.revision, user)

    assert saved.chapter == expected
    assert saved_again.chapter == expected


@pytest.mark.parametrize("revision", [None, LEGACY_REVISION])
def test_save_lines_writes_one_changelog_entry(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    user: User,
    revision: str,
) -> None:
    lines = create_lines_update(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)

    writer.save_lines(chapter.id_, lines, revision, user)

    assert count_chapter_changelog_entries(database) == 1


def test_save_lines_at_the_revision_of_the_previous_save(
    database: Database,
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    user: User,
) -> None:
    first_chapter = update_chapter(chapter, EDITED_INDEX)
    second_chapter = update_chapter(first_chapter, 0, OTHER_EDITED_NUMBER)
    first = writer.save_lines(
        chapter.id_, create_lines_update(first_chapter, EDITED_INDEX), None, user
    )

    second = writer.save_lines(
        chapter.id_, create_lines_update(second_chapter, 0), first.revision, user
    )

    assert second.revision == text_repository.find_chapter_revision(chapter.id_)
    assert second.revision != first.revision
    assert text_repository.find_chapter(chapter.id_).lines == second_chapter.lines
    assert count_chapter_changelog_entries(database) == 2


def test_save_lines_at_stale_revision(
    database: Database, writer: ChapterEditWriter, chapter: Chapter, user: User
) -> None:
    lines = create_lines_update(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)
    stored_chapter = find_stored_chapter(database, chapter)
    conflict = chapter_revision_conflict(chapter.id_, STALE_REVISION, LEGACY_REVISION)

    with pytest.raises(ConflictError, match=re.escape(str(conflict))):
        writer.save_lines(chapter.id_, lines, STALE_REVISION, user)

    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_save_lines_does_not_overwrite_a_concurrent_update(
    database: Database,
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    concurrent_chapter = update_chapter(chapter, 0, OTHER_EDITED_NUMBER)
    lines = create_lines_update(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)
    update_after_read(monkeypatch, text_repository, concurrent_chapter)

    with pytest.raises(ConflictError, match="expected revision legacy"):
        writer.save_lines(chapter.id_, lines, LEGACY_REVISION, ANY_USER)

    monkeypatch.undo()
    assert text_repository.find_chapter(chapter.id_).lines == concurrent_chapter.lines
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("revision", [None, LEGACY_REVISION])
def test_save_invalid_lines(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    user: User,
    revision: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(DataError):
        writer.save_lines(chapter.id_, create_invalid_update(chapter), revision, user)

    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("revision", [None, LEGACY_REVISION, STALE_REVISION])
def test_save_lines_of_unknown_chapter(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    user: User,
    revision: str,
) -> None:
    missing_id = attr.evolve(chapter.id_, name=f"{chapter.name} missing")
    lines = create_lines_update(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)

    with pytest.raises(NotFoundError, match=re.escape(f"Chapter {missing_id}")):
        writer.save_lines(missing_id, lines, revision, user)

    assert count_chapter_changelog_entries(database) == 0
