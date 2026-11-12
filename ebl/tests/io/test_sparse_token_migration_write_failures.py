from typing import Any, List, NoReturn, cast

from pymongo.collection import Collection
from pymongo.errors import AutoReconnect, BulkWriteError

from ebl.io.sparse_tokens.report import CollectionReport
from ebl.io.sparse_tokens.writes import BatchWriter


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


def test_a_failed_write_is_reported_per_document() -> None:
    report = CollectionReport("fragments")
    collection = FailingCollection()
    writer = BatchWriter(cast(Collection, collection), report)
    writer.add("A", {"text": 1}, 10)
    writer.add("B", {"text": 2}, 10)

    writer.flush()

    assert report.written == 1
    assert report.failed == {"B": "too large (code 10334)"}
    assert report.not_found == 0
    assert [len(batch) for batch in collection.batches] == [2]


class ConcernFailingCollection:
    def bulk_write(self, operations: List[Any], ordered: bool) -> NoReturn:
        raise BulkWriteError(
            {
                "nMatched": 2,
                "writeErrors": [],
                "writeConcernErrors": [{"errmsg": "timed out", "code": 64}],
            }
        )


class DisconnectedCollection:
    def bulk_write(self, operations: List[Any], ordered: bool) -> NoReturn:
        raise AutoReconnect("connection lost")


def test_a_write_concern_error_fails_the_whole_batch() -> None:
    report = CollectionReport("fragments")
    writer = BatchWriter(cast(Collection, ConcernFailingCollection()), report)
    writer.add("A", {"text": 1}, 10)
    writer.add("B", {"text": 2}, 10)

    writer.flush()

    assert (report.written, report.not_found) == (2, 0)
    assert report.failed == {
        "A": "not confirmed: timed out (code 64)",
        "B": "not confirmed: timed out (code 64)",
    }
    assert report.has_problems


def test_another_write_error_fails_the_batch_and_the_run_goes_on() -> None:
    report = CollectionReport("chapters")
    writer = BatchWriter(cast(Collection, DisconnectedCollection()), report)
    writer.add("A", {"lines": []}, 10)

    writer.flush()
    writer.add("B", {"lines": []}, 10)
    writer.flush()

    assert report.failed == {
        "A": "AutoReconnect: connection lost",
        "B": "AutoReconnect: connection lost",
    }
