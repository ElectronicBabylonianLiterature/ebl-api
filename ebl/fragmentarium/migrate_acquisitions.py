import logging
import os
import sys

from pymongo import MongoClient, UpdateOne

logger = logging.getLogger(__name__)

COLLECTION = "fragments"


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def build_update(document: dict) -> UpdateOne:
    acquisition = document.get("acquisition")
    if "acquisitions" in document:
        acquisitions = document["acquisitions"]
    else:
        acquisitions = [acquisition] if acquisition else []
    return UpdateOne(
        {"_id": document["_id"], "acquisition": acquisition},
        {"$set": {"acquisitions": acquisitions}, "$unset": {"acquisition": ""}},
    )


def collect_updates(collection) -> list[UpdateOne]:
    return [
        build_update(document)
        for document in collection.find({"acquisition": {"$exists": True}})
    ]


def _backfill_count(collection) -> int:
    return collection.count_documents(
        {"acquisition": {"$exists": False}, "acquisitions": {"$exists": False}}
    )


def run_migration(collection, dry_run: bool = False) -> dict:
    scanned = collection.count_documents({})
    updates = collect_updates(collection)
    if dry_run:
        backfilled = _backfill_count(collection)
        logger.info("[dry-run] no documents written")
    else:
        if updates:
            collection.bulk_write(updates)
        backfilled = collection.update_many(
            {"acquisition": {"$exists": False}, "acquisitions": {"$exists": False}},
            {"$set": {"acquisitions": []}},
        ).modified_count
    stats = {
        "scanned": scanned,
        "documents_migrated": len(updates),
        "documents_backfilled": backfilled,
    }
    logger.info(
        "Scanned %(scanned)s documents; migrated %(documents_migrated)s documents "
        "from 'acquisition' to 'acquisitions'; backfilled %(documents_backfilled)s "
        "documents with no acquisition data.",
        stats,
    )
    return stats


def main() -> dict:
    logging.basicConfig(level=logging.INFO)
    dry_run = "--dry-run" in sys.argv
    database = get_database()
    return run_migration(database[COLLECTION], dry_run=dry_run)


if __name__ == "__main__":
    main()
