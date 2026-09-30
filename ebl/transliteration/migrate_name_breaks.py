import argparse
import logging
import os
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Optional

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

COLLECTIONS = ("fragments", "texts", "chapters")
CACHE_COLLECTION = "cache"
BATCH_SIZE = 500
NAME_PART_TYPE = "ValueToken"
NAME_BREAK_TYPE = "BrokenAway"

NameToken = Mapping[str, object]


def get_database() -> Database:
    client: MongoClient = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ["MONGODB_DB"])


class NonAlternatingName(ValueError):
    pass


@dataclass(frozen=True)
class LegacyName:
    path: str
    name_parts: object


def _expected_type(index: int) -> str:
    return NAME_PART_TYPE if index % 2 == 0 else NAME_BREAK_TYPE


def _as_array(name_parts: object) -> Sequence[object]:
    if not isinstance(name_parts, Sequence) or isinstance(name_parts, (str, bytes)):
        raise NonAlternatingName(
            f"Expected nameParts to be an array, found {name_parts!r}. "
            f"There is nothing to split by position; refusing to migrate."
        )
    return name_parts


def _as_token(token: object, index: int) -> NameToken:
    expected = _expected_type(index)
    if not isinstance(token, Mapping) or token.get("type") != expected:
        raise NonAlternatingName(
            f"Expected a {expected} at position {index} of nameParts, "
            f"found {token!r}. Splitting by position would move it into "
            f"the wrong array; refusing to migrate."
        )
    return token


def _validate_ends_with_a_part(tokens: Sequence[NameToken]) -> None:
    if len(tokens) % 2 == 0:
        raise NonAlternatingName(
            f"Expected nameParts to start and end with a {NAME_PART_TYPE}, "
            f"found {len(tokens)} tokens. No name the parser writes has that "
            f"shape; refusing to migrate."
        )


def separate_name_parts(
    name_parts: object,
) -> tuple[list[NameToken], list[NameToken]]:
    tokens = [
        _as_token(token, index) for index, token in enumerate(_as_array(name_parts))
    ]
    _validate_ends_with_a_part(tokens)
    return tokens[0::2], tokens[1::2]


def _join(path: str, key: object) -> str:
    return f"{path}.{key}" if path else str(key)


def find_legacy_names(document: object, path: str = "") -> Iterator[LegacyName]:
    if isinstance(document, Mapping):
        yield from _legacy_names_in_object(document, path)
    elif isinstance(document, list):
        for index, value in enumerate(document):
            yield from find_legacy_names(value, _join(path, index))


def _legacy_names_in_object(
    document: Mapping[object, object], path: str
) -> Iterator[LegacyName]:
    is_legacy = "nameParts" in document and "nameBreaks" not in document
    if is_legacy:
        yield LegacyName(path, document["nameParts"])
    for key, value in document.items():
        if not (is_legacy and key == "nameParts"):
            yield from find_legacy_names(value, _join(path, key))


def _update_for(document_id: object, names: Sequence[LegacyName]) -> UpdateOne:
    unchanged_since_read: dict[str, object] = {"_id": document_id}
    separated: dict[str, object] = {}
    for name in names:
        parts, breaks = separate_name_parts(name.name_parts)
        unchanged_since_read[_join(name.path, "nameParts")] = name.name_parts
        unchanged_since_read[_join(name.path, "nameBreaks")] = {"$exists": False}
        separated[_join(name.path, "nameParts")] = parts
        separated[_join(name.path, "nameBreaks")] = breaks
    return UpdateOne(unchanged_since_read, {"$set": separated})


def _document_update(
    collection: Collection, document: Mapping[str, object]
) -> Optional[UpdateOne]:
    names = list(find_legacy_names(document))
    try:
        return _update_for(document["_id"], names) if names else None
    except NonAlternatingName as error:
        raise NonAlternatingName(
            f"{collection.name} document {document['_id']!r}: {error}"
        ) from error


def _pending_updates(collection: Collection) -> Iterator[UpdateOne]:
    for document in collection.find({}):
        update = _document_update(collection, document)
        if update is not None:
            yield update


@dataclass
class _Progress:
    attempted: int = 0
    written: int = 0


def _write_in_batches(
    collection: Collection, updates: Iterator[UpdateOne], progress: _Progress
) -> None:
    batch: list[UpdateOne] = []
    for update in updates:
        progress.attempted += 1
        batch.append(update)
        if len(batch) >= BATCH_SIZE:
            progress.written += collection.bulk_write(batch).matched_count
            batch = []
    if batch:
        progress.written += collection.bulk_write(batch).matched_count


def _apply_updates(collection: Collection, updates: Iterator[UpdateOne]) -> int:
    progress = _Progress()
    try:
        _write_in_batches(collection, updates, progress)
    except NonAlternatingName:
        _report_aborted(collection, progress.written)
        raise
    _report_skipped(collection, progress.attempted - progress.written)
    return progress.written


def _report_aborted(collection: Collection, written: int) -> None:
    logger.error(
        "%s: aborted; %s documents written before the abort stay migrated. "
        "Repair the document named below and run the migration again",
        collection.name,
        written,
    )


def _report_skipped(collection: Collection, skipped: int) -> None:
    if skipped:
        logger.warning(
            "%s: %s documents were changed or deleted while the migration was "
            "reading them and were left alone; run the migration again to pick "
            "up any that still hold a legacy name",
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


def clear_cache(database: Database, dry_run: bool) -> int:
    cache = database[CACHE_COLLECTION]
    if dry_run:
        cleared = cache.count_documents({})
    else:
        cleared = cache.delete_many({}).deleted_count
    logger.info(
        "%s: %s entries %s",
        CACHE_COLLECTION,
        cleared,
        "would be cleared" if dry_run else "cleared",
    )
    return cleared


def main(argv: Optional[Sequence[str]] = None) -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description=(
            "Separate the interleaved nameParts array into nameParts and "
            "nameBreaks, then clear the chapter display cache so it is rebuilt "
            "in the new shape. Documents already carrying nameBreaks are left "
            "alone, so the script is safe to re-run."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the changes; without it the script only reports counts",
    )
    arguments = parser.parse_args(argv)
    database = get_database()
    migrate(database, dry_run=not arguments.apply)
    clear_cache(database, dry_run=not arguments.apply)


if __name__ == "__main__":
    main()
