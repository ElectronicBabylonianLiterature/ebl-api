import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence

import bson
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.common import MAX_BSON_SIZE
from pymongo.database import Database
from pymongo.errors import PyMongoError

from ebl.io.sparse_tokens.documents import (
    STORED_SIZE,
    Rewrite,
    TokenFields,
    chapter_token_fields,
    fragment_token_fields,
    rewrite_document,
)
from ebl.io.sparse_tokens.report import CollectionReport
from ebl.io.sparse_tokens.writes import BatchWriter
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.provenance.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)

logger = logging.getLogger(__name__)

CACHE_COLLECTION = "cache"
READ_BATCH_SIZE = 20


def get_database() -> Database:
    client: MongoClient = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def all_token_fields(database: Database) -> List[TokenFields]:
    provenance_service = ProvenanceService(MongoProvenanceRepository(database))
    return [fragment_token_fields(), chapter_token_fields(provenance_service)]


def read_pipeline(token_fields: TokenFields) -> List[Dict[str, Any]]:
    size = {STORED_SIZE: {"$bsonSize": "$$ROOT"}}
    if token_fields.whole_document:
        return [{"$addFields": size}]
    return [{"$project": {**dict.fromkeys(token_fields.fields, 1), **size}}]


def encoded_size(fields: Mapping[str, Any]) -> int:
    return len(bson.encode(dict(fields)))


def size_after(document: Mapping[str, Any], fields: Mapping[str, Any]) -> int:
    original = {key: document[key] for key in fields}
    return document[STORED_SIZE] - encoded_size(original) + encoded_size(fields)


def checked_rewrite(
    token_fields: TokenFields,
    document: Mapping[str, Any],
    report: CollectionReport,
    full_check: bool,
) -> Optional[Rewrite]:
    document_id = str(document["_id"])
    try:
        rewrite = rewrite_document(token_fields, document, full_check)
    except Exception as error:
        report.unreadable[document_id] = f"{type(error).__name__}: {error}"[:500]
        return None
    if rewrite is None:
        report.unchanged += 1
    elif not rewrite.lossless:
        report.lossy.append(document_id)
    elif rewrite.dropped_keys:
        report.dropped_keys[document_id] = sorted(rewrite.dropped_keys)
    elif size_after(document, rewrite.fields) > MAX_BSON_SIZE:
        report.oversized[document_id] = size_after(document, rewrite.fields)
    else:
        return rewrite
    return None


def record_change(
    document: Mapping[str, Any], fields: Mapping[str, Any], report: CollectionReport
) -> int:
    size = size_after(document, fields)
    report.changed += 1
    report.bytes_before += document[STORED_SIZE]
    report.bytes_after += size
    return size


def migrate_collection(
    collection: Collection,
    token_fields: TokenFields,
    apply: bool,
    full_check: bool = False,
) -> CollectionReport:
    report = CollectionReport(token_fields.collection)
    writer = BatchWriter(collection, report)
    try:
        for document in collection.aggregate(
            read_pipeline(token_fields), batchSize=READ_BATCH_SIZE
        ):
            report.scanned += 1
            rewrite = checked_rewrite(token_fields, document, report, full_check)
            if rewrite is None:
                continue
            size = record_change(document, rewrite.fields, report)
            if apply:
                writer.add(document["_id"], rewrite.fields, size)
    except PyMongoError as error:
        report.interrupted = f"{type(error).__name__}: {error}"[:500]
    writer.flush()
    return report


def migrate(
    database: Database,
    apply: bool,
    collections: Sequence[str] = (),
    full_check: bool = False,
) -> List[CollectionReport]:
    existing = set(database.list_collection_names())
    reports = []
    for token_fields in all_token_fields(database):
        if collections and token_fields.collection not in collections:
            continue
        if token_fields.collection not in existing:
            logger.warning(
                "%s: no such collection; skipping it", token_fields.collection
            )
            continue
        report = migrate_collection(
            database[token_fields.collection], token_fields, apply, full_check
        )
        report.log(apply)
        reports.append(report)
    return reports


def clear_cache(database: Database, apply: bool) -> int:
    cache = database[CACHE_COLLECTION]
    cleared = (
        cache.delete_many({}).deleted_count if apply else cache.count_documents({})
    )
    logger.info(
        "%s: %d entries %s",
        CACHE_COLLECTION,
        cleared,
        "cleared" if apply else "would be cleared",
    )
    return cleared


def parse_arguments(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite the tokens of every fragment and chapter in the sparse "
            "storage shape (default values and derived fields omitted, legacy "
            "names split). Each document is loaded, dumped for storage, loaded "
            "again and compared before anything is written. Documents already "
            "in the sparse shape are left alone, so the script can be re-run."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the changes; without it the script only reports",
    )
    parser.add_argument(
        "--collection",
        action="append",
        choices=["fragments", "chapters"],
        default=[],
        help="limit the run to this collection (repeatable)",
    )
    parser.add_argument(
        "--full-check",
        action="store_true",
        help=(
            "load and verify every document, also those whose raw tokens are "
            "already sparse (slower; reports unreadable documents)"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    arguments = parse_arguments(argv)
    database = get_database()
    clear_cache(database, arguments.apply)
    reports = migrate(
        database, arguments.apply, arguments.collection, arguments.full_check
    )
    return 1 if any(report.has_problems for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
