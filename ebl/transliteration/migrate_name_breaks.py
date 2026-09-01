import argparse
import logging
import os
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTIONS = ("fragments", "texts", "chapters")
BATCH_SIZE = 500


def get_database() -> Database:
    client: MongoClient = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def separate_name_parts(name_parts: Sequence[Any]) -> Tuple[List[Any], List[Any]]:
    return list(name_parts[0::2]), list(name_parts[1::2])


def migrate_document(document: Any) -> bool:
    changed = False
    if isinstance(document, dict):
        if "nameParts" in document and "nameBreaks" not in document:
            parts, breaks = separate_name_parts(document["nameParts"])
            document["nameParts"] = parts
            document["nameBreaks"] = breaks
            changed = True
        for value in document.values():
            changed = migrate_document(value) or changed
    elif isinstance(document, list):
        for value in document:
            changed = migrate_document(value) or changed
    return changed


def _pending_updates(collection: Collection) -> Iterator[UpdateOne]:
    for document in collection.find({}):
        document_id = document["_id"]
        if migrate_document(document):
            del document["_id"]
            yield UpdateOne({"_id": document_id}, {"$set": document})


def migrate_collection(collection: Collection, dry_run: bool) -> int:
    migrated = 0
    batch: List[UpdateOne] = []
    for update in _pending_updates(collection):
        migrated += 1
        batch.append(update)
        if len(batch) >= BATCH_SIZE and not dry_run:
            collection.bulk_write(batch)
            batch = []
    if batch and not dry_run:
        collection.bulk_write(batch)
    return migrated


def migrate(database: Database, dry_run: bool) -> Mapping[str, int]:
    counts: Dict[str, int] = {}
    existing = set(database.list_collection_names())
    for name in COLLECTIONS:
        if name in existing:
            counts[name] = migrate_collection(database[name], dry_run)
            logger.info(
                "%s: %s documents %s",
                name,
                counts[name],
                "would be migrated" if dry_run else "migrated",
            )
    return counts


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Separate the interleaved nameParts array into nameParts and "
            "nameBreaks. Documents already carrying nameBreaks are left alone, "
            "so the script is safe to re-run."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the changes; without it the script only reports counts",
    )
    arguments = parser.parse_args(argv)
    migrate(get_database(), dry_run=not arguments.apply)


if __name__ == "__main__":
    main()
