import argparse
import json
import os
from typing import Optional, Sequence

from bson import ObjectId
from pymongo import MongoClient, ReadPreference
from pymongo.database import Database

from ebl.cache.application.custom_cache import CHAPTER_CACHE_KEY_PREFIX
from ebl.cache.infrastructure.mongo_chapter_cache_state import COLLECTION


def clear_versioned_chapter_cache(database: Database, repair_pending: bool) -> dict:
    cleared = database["cache"].delete_many(
        {"cache_key": {"$regex": f"^{CHAPTER_CACHE_KEY_PREFIX}"}}
    )
    repaired = 0
    if repair_pending:
        repaired = (
            database[COLLECTION]
            .update_many(
                {"pending": {"$ne": 0}},
                {
                    "$set": {"pending": 0, "epoch": str(ObjectId())},
                    "$inc": {"revision": 1},
                },
            )
            .modified_count
        )
    return {"clearedEntries": cleared.deleted_count, "repairedChapters": repaired}


def main(arguments: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Clear private chapter cache payloads during deployment or rollback. "
        "Stop all old and new chapter readers, writers and batch jobs, then wait for "
        "every in-flight request and job to finish before running this command. "
        "Start only workers participating in the new protocol after completion."
    )
    parser.add_argument(
        "--uri-env", required=True, help="Environment variable holding the MongoDB URI"
    )
    parser.add_argument("--database", required=True)
    parser.add_argument("--confirm-quiescent", required=True, action="store_true")
    parser.add_argument(
        "--repair-pending",
        action="store_true",
        help="Recover abandoned pending writers only after all writers and readers have stopped. "
        "Without this option revision and pending metadata are preserved.",
    )
    options = parser.parse_args(arguments)
    with MongoClient(
        os.environ[options.uri_env], read_preference=ReadPreference.PRIMARY
    ) as client:
        result = clear_versioned_chapter_cache(
            client[options.database], options.repair_pending
        )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
