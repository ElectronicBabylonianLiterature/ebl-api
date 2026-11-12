import logging
from typing import Any, Dict, Iterator, List, cast

import pytest
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import AutoReconnect

from ebl.io.sparse_tokens.documents import fragment_token_fields
from ebl.io.sparse_tokens.migrate import migrate_collection
from ebl.io.sparse_tokens.report import CollectionReport
from ebl.io.sparse_tokens.writes import BatchWriter
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.fragmentarium.stored_line_shapes import sparse_tokens
from ebl.tests.io.sparse_token_migration_fixtures import (
    FRAGMENT,
    full_fragment_document,
    insert_full_documents,
    stored_fragment,
)


class InterruptedCollection:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def aggregate(
        self, pipeline: List[Dict[str, Any]], batchSize: int
    ) -> Iterator[Dict[str, Any]]:
        yield from self._collection.aggregate(pipeline, batchSize=batchSize)
        raise AutoReconnect("connection lost")

    def bulk_write(self, operations: List[Any], ordered: bool) -> Any:
        return self._collection.bulk_write(operations, ordered=ordered)


@pytest.fixture
def interrupted_report(
    database: Database, seeded_provenance_service: ProvenanceService
) -> CollectionReport:
    insert_full_documents(database, seeded_provenance_service)
    collection = cast(Collection, InterruptedCollection(database.fragments))
    return migrate_collection(collection, fragment_token_fields(), apply=True)


def test_a_read_error_is_reported(interrupted_report: CollectionReport) -> None:
    assert interrupted_report.interrupted == "AutoReconnect: connection lost"
    assert interrupted_report.has_problems


def test_a_read_error_still_writes_the_staged_documents(
    database: Database,
    seeded_provenance_service: ProvenanceService,
    interrupted_report: CollectionReport,
) -> None:
    full_fragment = full_fragment_document(FRAGMENT, seeded_provenance_service)

    assert (interrupted_report.changed, interrupted_report.written) == (1, 1)
    assert stored_fragment(database)["text"] == sparse_tokens(full_fragment["text"])


def test_a_read_error_is_logged(
    interrupted_report: CollectionReport, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        interrupted_report.log(apply=True)

    assert "fragments: scan stopped early: AutoReconnect: connection lost" in (
        caplog.messages
    )


def test_an_update_that_matches_no_document_is_reported(database: Database) -> None:
    database.fragments.insert_one({"_id": "present"})
    report = CollectionReport("fragments")
    writer = BatchWriter(database.fragments, report)
    writer.add("present", {"text": 1}, 10)
    writer.add("deleted", {"text": 2}, 10)

    writer.flush()

    assert (report.written, report.not_found, report.failed) == (1, 1, {})
    assert report.has_problems


def test_an_update_that_matches_no_document_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    report = CollectionReport("chapters", not_found=2)

    with caplog.at_level(logging.ERROR):
        report.log(apply=True)

    assert "chapters: 2 updates matched no document (deleted during the run?)" in (
        caplog.messages
    )


def test_a_clean_report_has_no_problems() -> None:
    assert not CollectionReport("fragments").has_problems
