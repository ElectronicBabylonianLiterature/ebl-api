"""One-off migration for the nameParts/nameBreaks split.

A named sign used to store its name as one interleaved array, mixing the value
tokens with the brackets that fall inside the name. They are now two arrays,
`nameParts` and `nameBreaks`. This separates existing documents.

Run it only after the backend that understands both shapes is deployed: older
code rejects an unknown `nameBreaks` field outright.

    poetry run python -m ebl.transliteration.migrate_name_breaks           # dry run
    poetry run python -m ebl.transliteration.migrate_name_breaks --apply   # writes

It writes only the top-level fields it changed, and only to documents that have
not been touched since it read them, so an edit made while the scan is running
is left alone instead of being reverted. Those documents are reported and are
picked up by the next run.

The script is resumable. A document that already carries `nameBreaks` is
skipped, so if a run stops early — `NonAlternatingName` aborts it on data that
does not alternate — the fix is to repair the document the error names and run
it again. Nothing already written is undone or written twice.

Both MONGODB_URI and MONGODB_DB must be set.
"""

import argparse
import copy
import logging
import os
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTIONS = ("fragments", "texts", "chapters")
BATCH_SIZE = 500
NAME_PART_TYPE = "ValueToken"
NAME_BREAK_TYPE = "BrokenAway"

NameToken = Mapping[str, Any]
MongoDocument = Mapping[str, Any]


def get_database() -> Database:
    client: MongoClient = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ["MONGODB_DB"])


class NonAlternatingName(ValueError):
    """A legacy nameParts array that does not alternate part, break, part."""


def _expected_type(index: int) -> str:
    return NAME_PART_TYPE if index % 2 == 0 else NAME_BREAK_TYPE


def _validate_is_an_array(name_parts: Any) -> None:
    if not isinstance(name_parts, Sequence) or isinstance(name_parts, (str, bytes)):
        raise NonAlternatingName(
            f"Expected nameParts to be an array, found {name_parts!r}. "
            f"There is nothing to split by position; refusing to migrate."
        )


def _validate_alternating(name_parts: Sequence[Any]) -> None:
    for index, token in enumerate(name_parts):
        expected = _expected_type(index)
        if not isinstance(token, Mapping) or token.get("type") != expected:
            raise NonAlternatingName(
                f"Expected a {expected} at position {index} of nameParts, "
                f"found {token!r}. Splitting by position would move it into "
                f"the wrong array; refusing to migrate."
            )


def separate_name_parts(
    name_parts: Any,
) -> tuple[list[NameToken], list[NameToken]]:
    _validate_is_an_array(name_parts)
    _validate_alternating(name_parts)
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


def _migrate_copy(
    collection: Collection, document: MongoDocument
) -> Optional[dict[str, Any]]:
    migrated = copy.deepcopy(dict(document))
    try:
        changed = migrate_document(migrated)
    except NonAlternatingName as error:
        raise NonAlternatingName(
            f"{collection.name} document {document['_id']!r}: {error}"
        ) from error
    return migrated if changed else None


def _update_for(original: MongoDocument, migrated: MongoDocument) -> UpdateOne:
    changed = {
        key: value
        for key, value in migrated.items()
        if key != "_id" and value != original[key]
    }
    unchanged_since_read: dict[str, Any] = {"_id": original["_id"]}
    for key in changed:
        unchanged_since_read[key] = original[key]
    return UpdateOne(unchanged_since_read, {"$set": changed})


def _pending_updates(collection: Collection) -> Iterator[UpdateOne]:
    for document in collection.find({}):
        migrated = _migrate_copy(collection, document)
        if migrated is not None:
            yield _update_for(document, migrated)


def _apply_updates(collection: Collection, updates: Iterator[UpdateOne]) -> int:
    attempted = 0
    written = 0
    batch: list[UpdateOne] = []
    for update in updates:
        attempted += 1
        batch.append(update)
        if len(batch) >= BATCH_SIZE:
            written += collection.bulk_write(batch).matched_count
            batch = []
    if batch:
        written += collection.bulk_write(batch).matched_count
    _report_skipped(collection, attempted - written)
    return written


def _report_skipped(collection: Collection, skipped: int) -> None:
    if skipped:
        logger.warning(
            "%s: %s documents changed while the migration was reading them and "
            "were left alone; run the migration again to pick them up",
            collection.name,
            skipped,
        )


def migrate_collection(collection: Collection, dry_run: bool) -> int:
    if dry_run:
        return sum(1 for _ in _pending_updates(collection))
    return _apply_updates(collection, _pending_updates(collection))


def migrate(database: Database, dry_run: bool) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    existing = set(database.list_collection_names())
    for name in COLLECTIONS:
        if name not in existing:
            logger.warning(
                "%s: no such collection in database %r; skipping it",
                name,
                database.name,
            )
            continue
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
