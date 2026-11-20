import re
from typing import Callable

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.corpus import CorpusDependencies
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.errors import ConflictError, DataError, NotFoundError
from ebl.tests.corpus.chapter_edit_support import ChapterEdit, ChapterEditKind
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
)
from ebl.tests.corpus.outline_support import create_outline_chapter
from ebl.tests.corpus.support import ANY_USER

REVISIONS = (None, LEGACY_REVISION)


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


@pytest.fixture
def writer(corpus_dependencies: CorpusDependencies) -> ChapterEditWriter:
    return ChapterEditWriter(corpus_dependencies)


@pytest.mark.parametrize("revision", REVISIONS)
def test_save_returns_the_chapter_the_corpus_returns(
    writer: ChapterEditWriter,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    save_sibling_with_corpus: Callable[[Chapter, ChapterEdit], Chapter],
    revision: str,
) -> None:
    edit = edit_kind.create_edit(chapter, 0)
    expected = save_sibling_with_corpus(chapter, edit)

    saved = edit.save(writer, chapter.id_, revision, ANY_USER)

    assert saved.chapter == expected
    assert saved.chapter != chapter
    assert writer.find_chapter(chapter.id_) == expected


@pytest.mark.parametrize("revision", REVISIONS)
def test_save_returns_the_stored_revision(
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    revision: str,
) -> None:
    saved = edit_kind.create_edit(chapter, 0).save(
        writer, chapter.id_, revision, ANY_USER
    )

    assert saved.revision == text_repository.find_chapter_revision(chapter.id_)
    assert saved.revision != LEGACY_REVISION


@pytest.mark.parametrize("revision", REVISIONS)
def test_save_writes_one_changelog_entry(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    revision: str,
) -> None:
    edit_kind.create_edit(chapter, 0).save(writer, chapter.id_, revision, ANY_USER)

    assert count_chapter_changelog_entries(database) == 1


def test_save_at_the_revision_of_the_previous_save(
    database: Database,
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    first = edit_kind.create_edit(chapter, 0).save(writer, chapter.id_, None, ANY_USER)

    second = edit_kind.create_edit(first.chapter, 1).save(
        writer, chapter.id_, first.revision, ANY_USER
    )

    assert second.revision == text_repository.find_chapter_revision(chapter.id_)
    assert second.revision != first.revision
    assert second.chapter != first.chapter
    assert writer.find_chapter(chapter.id_) == second.chapter
    assert count_chapter_changelog_entries(database) == 2


def test_save_at_stale_revision(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    conflict = chapter_revision_conflict(chapter.id_, STALE_REVISION, LEGACY_REVISION)

    with pytest.raises(ConflictError, match=re.escape(str(conflict))):
        edit_kind.create_edit(chapter, 0).save(
            writer, chapter.id_, STALE_REVISION, ANY_USER
        )

    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_save_does_not_overwrite_a_concurrent_update(
    database: Database,
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    find_chapter = text_repository.find_chapter

    def find_chapter_before_concurrent_update(id_: ChapterId) -> Chapter:
        found_chapter = find_chapter(id_)
        text_repository.update(id_, chapter)
        return found_chapter

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            text_repository, "find_chapter", find_chapter_before_concurrent_update
        )
        with pytest.raises(ConflictError, match="expected revision legacy"):
            edit_kind.create_edit(chapter, 0).save(
                writer, chapter.id_, LEGACY_REVISION, ANY_USER
            )

    concurrent_revision = text_repository.find_chapter_revision(chapter.id_)
    assert concurrent_revision != LEGACY_REVISION
    assert text_repository.find_chapter(chapter.id_).lines == chapter.lines
    assert writer.find_manuscripts(chapter.id_) == chapter.manuscripts
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("revision", REVISIONS)
def test_save_invalid_edit(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    revision: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(DataError):
        edit_kind.create_invalid_edit(chapter).save(
            writer, chapter.id_, revision, ANY_USER
        )

    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("revision", [None, LEGACY_REVISION, STALE_REVISION])
def test_save_unknown_chapter(
    database: Database,
    writer: ChapterEditWriter,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    revision: str,
) -> None:
    missing_id = attr.evolve(chapter.id_, name=f"{chapter.name} missing")

    with pytest.raises(NotFoundError, match=re.escape(f"Chapter {missing_id}")):
        edit_kind.create_edit(chapter, 0).save(writer, missing_id, revision, ANY_USER)

    assert count_chapter_changelog_entries(database) == 0
