"""
Seed script for the realia collection — development only.

Usage:
    poetry run python scripts/seed_realia.py [--delete]

Options:
    --delete    Remove the seeded documents instead of inserting them.

Credentials are read from MONGODB_URI and MONGODB_DB environment variables
(set them in .env or export them before running). No secrets are hard-coded.

WARNING: Remove this script and any seeded documents before merging to master.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from pymongo import MongoClient
except ImportError:
    sys.exit("pymongo not found — run inside the poetry environment: poetry run python scripts/seed_realia.py")

SEED_FILE = Path(__file__).parent.parent / "realia-seed-pig.json"


def get_db():
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB")
    if not uri or not db_name:
        sys.exit("MONGODB_URI and MONGODB_DB must be set in the environment (check .env).")
    client = MongoClient(uri)
    return client, client[db_name]


def seed(db) -> None:
    with open(SEED_FILE) as f:
        doc = json.load(f)
    result = db["realia"].replace_one({"_id": doc["_id"]}, doc, upsert=True)
    if result.upserted_id:
        print(f"Inserted: {result.upserted_id}")
    else:
        print(f"Updated existing document: {doc['_id']} (matched={result.matched_count})")


def delete(db) -> None:
    with open(SEED_FILE) as f:
        doc = json.load(f)
    result = db["realia"].delete_one({"_id": doc["_id"]})
    print(f"Deleted {result.deleted_count} document(s) with _id='{doc['_id']}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or unseed realia dev data.")
    parser.add_argument("--delete", action="store_true", help="Remove seed documents instead of inserting.")
    args = parser.parse_args()

    # Load .env if present, without using python-dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    client, db = get_db()
    try:
        if args.delete:
            delete(db)
        else:
            seed(db)
    finally:
        client.close()


if __name__ == "__main__":
    main()
