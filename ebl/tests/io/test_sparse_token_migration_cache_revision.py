import pytest
from pymongo.database import Database

from ebl.io.sparse_tokens.migrate import migrate
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.fragmentarium.stored_line_shapes import sparse_tokens
from ebl.tests.io.sparse_token_migration_fixtures import (
    CHAPTER,
    full_chapter_document,
    insert_full_documents,
    stored_chapter,
)

CACHE_REVISION = "6740a1b2c3d4e5f6a7b8c9d0"


@pytest.fixture
def full_database(
    database: Database, seeded_provenance_service: ProvenanceService
) -> Database:
    insert_full_documents(database, seeded_provenance_service)
    return database


def set_cache_revision(database: Database) -> None:
    database.chapters.update_one({}, {"$set": {"_cacheRevision": CACHE_REVISION}})


@pytest.mark.parametrize("full_check", [False, True])
def test_a_dense_chapter_with_a_cache_revision_is_migrated(
    full_database: Database, full_check: bool
) -> None:
    set_cache_revision(full_database)

    [report] = migrate(
        full_database, apply=True, collections=["chapters"], full_check=full_check
    )

    assert (report.changed, report.written) == (1, 1)
    assert not report.has_problems
    chapter = stored_chapter(full_database)
    assert chapter["_cacheRevision"] == CACHE_REVISION
    assert chapter["lines"] == sparse_tokens(full_chapter_document(CHAPTER)["lines"])


def test_a_sparse_chapter_with_a_cache_revision_passes_the_full_check(
    full_database: Database,
) -> None:
    migrate(full_database, apply=True, collections=["chapters"])
    set_cache_revision(full_database)
    before = stored_chapter(full_database)

    [report] = migrate(
        full_database, apply=True, collections=["chapters"], full_check=True
    )

    assert (report.scanned, report.unchanged, report.changed) == (1, 1, 0)
    assert not report.has_problems
    assert stored_chapter(full_database) == before
