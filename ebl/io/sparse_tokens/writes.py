from typing import Any, Dict, List

from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, PyMongoError

from ebl.io.sparse_tokens.report import CollectionReport

BATCH_BYTES = 16 * 1024 * 1024
BATCH_OPERATIONS = 100


class BatchWriter:
    def __init__(self, collection: Collection, report: CollectionReport) -> None:
        self._collection = collection
        self._report = report
        self._document_ids: List[Any] = []
        self._operations: List[UpdateOne] = []
        self._bytes = 0

    def add(self, document_id: Any, fields: Dict[str, Any], size: int) -> None:
        self._document_ids.append(document_id)
        self._operations.append(UpdateOne({"_id": document_id}, {"$set": fields}))
        self._bytes += size
        if len(self._operations) >= BATCH_OPERATIONS or self._bytes >= BATCH_BYTES:
            self.flush()

    def flush(self) -> None:
        if not self._operations:
            return
        document_ids, operations = self._document_ids, self._operations
        self._document_ids, self._operations, self._bytes = [], [], 0
        try:
            result = self._collection.bulk_write(operations, ordered=False)
            self._record_matched(len(operations), result.matched_count, 0)
        except BulkWriteError as error:
            self._record_bulk_failures(document_ids, error)
        except PyMongoError as error:
            self._record_batch_failure(document_ids, f"{type(error).__name__}: {error}")

    def _record_matched(self, operations: int, matched: int, errors: int) -> None:
        self._report.written += matched
        self._report.not_found += operations - matched - errors

    def _record_bulk_failures(
        self, document_ids: List[Any], error: BulkWriteError
    ) -> None:
        write_errors = error.details.get("writeErrors", [])
        self._record_matched(
            len(document_ids), error.details.get("nMatched", 0), len(write_errors)
        )
        for write_error in write_errors:
            self._report.failed[str(document_ids[write_error["index"]])] = (
                f"{write_error.get('errmsg')} (code {write_error.get('code')})"
            )
        concern_errors = error.details.get("writeConcernErrors", [])
        if concern_errors:
            message = "; ".join(
                f"{concern.get('errmsg')} (code {concern.get('code')})"
                for concern in concern_errors
            )
            self._record_batch_failure(document_ids, f"not confirmed: {message}")

    def _record_batch_failure(self, document_ids: List[Any], message: str) -> None:
        for document_id in document_ids:
            self._report.failed.setdefault(str(document_id), message)
