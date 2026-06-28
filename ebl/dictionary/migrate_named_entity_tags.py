import logging
import os
import sys
from typing import Iterable

from pymongo import MongoClient, UpdateOne

logger = logging.getLogger(__name__)

COLLECTION = "words"
NAMED_ENTITY_CODES = frozenset(
    "AN CN DN EN FN GN KN LN MN ON PN QN RN SN TN WN YN".split()
)


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def deduplicate(tags: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def split_pos(pos: list[str]) -> tuple[list[str], list[str]]:
    grammatical = [tag for tag in pos if tag not in NAMED_ENTITY_CODES]
    named = [tag for tag in pos if tag in NAMED_ENTITY_CODES]
    return grammatical, named


def build_update(document: dict) -> tuple[UpdateOne, int]:
    pos = document.get("pos", [])
    grammatical, named = split_pos(pos)
    merged = deduplicate([*document.get("namedEntityTags", []), *named])
    update = UpdateOne(
        {"_id": document["_id"]},
        {"$set": {"pos": grammatical, "namedEntityTags": merged}},
    )
    return update, len(named)


def collect_updates(collection) -> tuple[list[UpdateOne], int]:
    updates: list[UpdateOne] = []
    moved_tags = 0
    for document in collection.find({"pos": {"$in": list(NAMED_ENTITY_CODES)}}):
        update, moved = build_update(document)
        updates.append(update)
        moved_tags += moved
    return updates, moved_tags


def _backfill_count(collection) -> int:
    return collection.count_documents(
        {
            "namedEntityTags": {"$exists": False},
            "pos": {"$nin": list(NAMED_ENTITY_CODES)},
        }
    )


def run_migration(collection, dry_run: bool = False) -> dict:
    scanned = collection.count_documents({})
    updates, moved_tags = collect_updates(collection)
    if dry_run:
        backfilled = _backfill_count(collection)
        logger.info("[dry-run] no documents written")
    else:
        if updates:
            collection.bulk_write(updates)
        backfilled = collection.update_many(
            {"namedEntityTags": {"$exists": False}},
            {"$set": {"namedEntityTags": []}},
        ).modified_count
    stats = {
        "scanned": scanned,
        "documents_with_moved_tags": len(updates),
        "tags_moved": moved_tags,
        "documents_backfilled": backfilled,
    }
    logger.info(
        "Scanned %(scanned)s documents; moved %(tags_moved)s tags in "
        "%(documents_with_moved_tags)s documents; backfilled "
        "%(documents_backfilled)s documents.",
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
