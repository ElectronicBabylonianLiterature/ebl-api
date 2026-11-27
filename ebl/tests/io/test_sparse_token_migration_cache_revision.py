from typing import Any, Mapping, Optional

import pytest
from pymongo.database import Database

from ebl.io.sparse_tokens import migrate as migrate_module
from ebl.io.sparse_tokens.documents import Rewrite, TokenFields
from ebl.io.sparse_tokens.migrate import migrate
from ebl.io.sparse_tokens.report import CollectionReport
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.fragmentarium.stored_line_shapes import sparse_tokens
from ebl.tests.io.sparse_token_migration_fixtures import (
    CHAPTER,
    full_chapter_document,
    insert_full_documents,
    stored_chapter,
)

CACHE_REVISION = "6740a1b2c3d4e5f6a7b8c9d0"
EDITED_REVISION = "6740a1b2c3d4e5f6a7b8c9d1"
EDITED_LINES = [{"number": "edited during the run"}]


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


def edit_after_reading(monkeypatch: pytest.MonkeyPatch, database: Database) -> None:
    checked_rewrite = migrate_module.checked_rewrite

    def read_then_edit(
        token_fields: TokenFields,
        document: Mapping[str, Any],
        report: CollectionReport,
        full_check: bool,
    ) -> Optional[Rewrite]:
        rewrite = checked_rewrite(token_fields, document, report, full_check)
        database.chapters.update_one(
            {"_id": document["_id"]},
            {"$set": {"lines": EDITED_LINES, "_cacheRevision": EDITED_REVISION}},
        )
        return rewrite

    monkeypatch.setattr(migrate_module, "checked_rewrite", read_then_edit)


@pytest.mark.parametrize("has_cache_revision", [False, True])
def test_a_chapter_edited_during_the_run_is_not_overwritten(
    full_database: Database,
    monkeypatch: pytest.MonkeyPatch,
    has_cache_revision: bool,
) -> None:
    if has_cache_revision:
        set_cache_revision(full_database)
    edit_after_reading(monkeypatch, full_database)

    [report] = migrate(full_database, apply=True, collections=["chapters"])

    assert (report.changed, report.written, report.not_found) == (1, 0, 1)
    assert report.has_problems
    chapter = stored_chapter(full_database)
    assert chapter["_cacheRevision"] == EDITED_REVISION
    assert chapter["lines"] == EDITED_LINES
