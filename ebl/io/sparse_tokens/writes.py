from typing import Any, Dict, List

from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

from ebl.io.sparse_tokens.report import CollectionReport

BATCH_BYTES = 16 * 1024 * 1024
BATCH_OPERATIONS = 100


class BatchWriter:
    def __init__(self, collection: Collection, report: CollectionReport) -> None:
        self._collection = collection
        self._report = report
        self._ids: List[Any] = []
        self._operations: List[UpdateOne] = []
        self._bytes = 0

    def add(self, document_id: Any, fields: Dict[str, Any], size: int) -> None:
        self._ids.append(document_id)
        self._operations.append(UpdateOne({"_id": document_id}, {"$set": fields}))
        self._bytes += size
        if len(self._operations) >= BATCH_OPERATIONS or self._bytes >= BATCH_BYTES:
            self.flush()

    def flush(self) -> None:
        if not self._operations:
            return
        ids, operations = self._ids, self._operations
        self._ids, self._operations, self._bytes = [], [], 0
        try:
            result = self._collection.bulk_write(operations, ordered=False)
            self._report.written += result.matched_count
        except BulkWriteError as error:
            self._record_failures(ids, error)

    def _record_failures(self, ids: List[Any], error: BulkWriteError) -> None:
        self._report.written += error.details.get("nMatched", 0)
        for write_error in error.details.get("writeErrors", []):
            self._report.failed[str(ids[write_error["index"]])] = (
                f"{write_error.get('errmsg')} (code {write_error.get('code')})"
            )
