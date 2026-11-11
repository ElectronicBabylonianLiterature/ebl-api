import io
import logging
import runpy
import sys
from contextlib import redirect_stdout
from typing import Any, List, NoReturn, cast

import pytest
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError

from ebl.io.sparse_tokens import migrate as migrate_module
from ebl.io.sparse_tokens.documents import STORED_SIZE, TokenFields
from ebl.io.sparse_tokens.migrate import (
    get_database,
    main,
    migrate_collection,
    read_pipeline,
)
from ebl.io.sparse_tokens.report import CollectionReport
from ebl.io.sparse_tokens.writes import BatchWriter
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.io.sparse_token_migration_fixtures import insert_full_documents


class FailingCollection:
    def __init__(self) -> None:
        self.batches: List[List[Any]] = []

    def bulk_write(self, operations: List[Any], ordered: bool) -> NoReturn:
        self.batches.append(operations)
        raise BulkWriteError(
            {
                "nMatched": 1,
                "writeErrors": [{"index": 1, "errmsg": "too large", "code": 10334}],
            }
        )


class WriteResult:
    matched_count = 1


class RecordingCollection:
    def __init__(self) -> None:
        self.batches: List[List[Any]] = []

    def bulk_write(self, operations: List[Any], ordered: bool) -> WriteResult:
        self.batches.append(operations)
        return WriteResult()


def test_a_failed_write_is_reported_per_document() -> None:
    report = CollectionReport("fragments")
    collection = FailingCollection()
    writer = BatchWriter(cast(Collection, collection), report)
    writer.add("A", {"text": 1}, 10)
    writer.add("B", {"text": 2}, 10)

    writer.flush()

    assert report.written == 1
    assert report.failed == {"B": "too large (code 10334)"}
    assert [len(batch) for batch in collection.batches] == [2]


@pytest.mark.parametrize("setting,value", [("BATCH_OPERATIONS", 1), ("BATCH_BYTES", 5)])
def test_the_writer_flushes_full_batches(
    monkeypatch: pytest.MonkeyPatch, setting: str, value: int
) -> None:
    monkeypatch.setattr(f"ebl.io.sparse_tokens.writes.{setting}", value)
    collection = RecordingCollection()
    report = CollectionReport("chapters")
    writer = BatchWriter(cast(Collection, collection), report)

    writer.add("A", {"lines": []}, 10)
    writer.add("B", {"lines": []}, 10)
    writer.flush()

    assert [len(batch) for batch in collection.batches] == [1, 1]
    assert report.written == 2


def test_an_empty_writer_writes_nothing() -> None:
    collection = FailingCollection()

    BatchWriter(cast(Collection, collection), CollectionReport("chapters")).flush()

    assert collection.batches == []


def test_read_pipelines_add_the_stored_size() -> None:
    fragments = TokenFields(
        "fragments", ("text",), lambda document: document, lambda value: {}, False
    )
    chapters = TokenFields(
        "chapters", ("lines",), lambda document: document, lambda value: {}, True
    )
    size = {STORED_SIZE: {"$bsonSize": "$$ROOT"}}

    assert read_pipeline(fragments) == [{"$project": {"text": 1, **size}}]
    assert read_pipeline(chapters) == [{"$addFields": size}]


def test_the_report_logs_every_problem(caplog: pytest.LogCaptureFixture) -> None:
    report = CollectionReport("fragments", lossy=["A"], failed={"B": "error"})
    caplog.set_level(logging.INFO)

    report.log(apply=True)

    assert "1 documents are not lossless" in caplog.text
    assert "('B', 'error')" in caplog.text
    assert "  A" in caplog.text


def test_migrate_collection_counts_scanned_documents(database: Database) -> None:
    database.fragments.insert_one({"_id": "X.1"})
    spec = TokenFields(
        "fragments", ("text",), lambda document: document, lambda value: {}, False
    )

    report = migrate_collection(database.fragments, spec, apply=True)

    assert (report.scanned, report.unchanged) == (1, 1)


@pytest.mark.parametrize("arguments,expected_writes", [([], 0), (["--apply"], 2)])
def test_main_runs_the_migration(
    database: Database,
    seeded_provenance_service: ProvenanceService,
    monkeypatch: pytest.MonkeyPatch,
    arguments: List[str],
    expected_writes: int,
) -> None:
    insert_full_documents(database, seeded_provenance_service)
    monkeypatch.setattr(migrate_module, "get_database", lambda: database)
    seen = []
    original = migrate_module.migrate

    def recording_migrate(*args: Any, **kwargs: Any) -> List[CollectionReport]:
        reports = original(*args, **kwargs)
        seen.extend(reports)
        return reports

    monkeypatch.setattr(migrate_module, "migrate", recording_migrate)

    assert main(arguments) == 0
    assert sum(report.written for report in seen) == expected_writes


def test_main_fails_when_a_document_has_a_problem(
    database: Database,
    seeded_provenance_service: ProvenanceService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    insert_full_documents(database, seeded_provenance_service)
    database.fragments.update_one({}, {"$set": {"text.lines": "not lines"}})
    monkeypatch.setattr(migrate_module, "get_database", lambda: database)

    assert main(["--collection", "fragments", "--full-check"]) == 1


def test_get_database_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:1")
    monkeypatch.setenv("MONGODB_DB", "scratch_name")

    assert get_database().name == "scratch_name"


def test_a_lossy_document_is_reported_and_not_written(database: Database) -> None:
    original = [{"type": "Reading", "value": "ku", "flags": []}]
    database.fragments.insert_one({"_id": "X.1", "text": original})
    spec = TokenFields(
        "fragments",
        ("text",),
        lambda document: document["text"],
        lambda text: {"text": "changed"},
        False,
    )

    report = migrate_collection(database.fragments, spec, apply=True)

    stored = database.fragments.find_one({"_id": "X.1"})
    assert report.lossy == ["X.1"]
    assert stored is not None
    assert stored["text"] == original


def test_running_the_migration_module_calls_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["migrate", "--help"])
    monkeypatch.delitem(sys.modules, "ebl.io.sparse_tokens.migrate", raising=False)
    output = io.StringIO()

    with pytest.raises(SystemExit) as exit_info, redirect_stdout(output):
        runpy.run_module("ebl.io.sparse_tokens.migrate", run_name="__main__")

    assert exit_info.value.code == 0
    assert "--apply" in output.getvalue()
