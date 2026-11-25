from collections.abc import Callable

import pytest
from bson.int64 import Int64
from pymongo.database import Database

from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_preflight import (
    assert_apply_ready,
    index_matches,
)
from ebl.media.infrastructure.backfill_runner import LegacyPhotoMigration
from ebl.media.infrastructure.media_indexes import MediaIndexDefinition

FRAGMENT_KEYS = [("associations.fragmentId", 1), ("state", 1)]


def test_index_matching_ignores_server_bookkeeping() -> None:
    definition = MediaIndexDefinition("media", "source", (("sourceKey", 1),))
    information = {
        "key": [("sourceKey", 1)],
        "v": 99,
        "ns": "server.collection",
        "background": True,
    }
    assert index_matches(information, definition)


def database_state(database: Database) -> dict:
    return {
        name: {
            "documents": list(database[name].find()),
            "indexes": database[name].index_information(),
        }
        for name in database.list_collection_names()
    }


@pytest.fixture
def prepared_migration(
    legacy_photo: Callable, migration_factory: Callable
) -> LegacyPhotoMigration:
    legacy_photo()
    return migration_factory()


def assert_rejected_without_writes(migration: LegacyPhotoMigration) -> None:
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    assert candidate.outcome == "candidate"
    before = database_state(migration.sources.database)
    with pytest.raises(ValueError):
        migration.apply(candidate)
    assert database_state(migration.sources.database) == before


@pytest.mark.parametrize(
    "case",
    [
        ("media", "media_fragment_state", [("caption", 1)], {}),
        ("media", "media_fragment_state", list(reversed(FRAGMENT_KEYS)), {}),
        ("media", "media_fragment_state", FRAGMENT_KEYS, {"unique": True}),
        ("media.chunks", "files_id_1_n_1", [("files_id", 1), ("n", 1)], {}),
        ("media", "media_fragment_state", FRAGMENT_KEYS, {"sparse": True}),
        (
            "media",
            "media_fragment_state",
            FRAGMENT_KEYS,
            {"partialFilterExpression": {"state": {"$exists": True}}},
        ),
        ("media", "media_fragment_state", FRAGMENT_KEYS, {"hidden": True}),
        (
            "media",
            "media_fragment_state",
            FRAGMENT_KEYS,
            {"collation": {"locale": "en"}},
        ),
    ],
    ids=[
        "wrong-key",
        "wrong-order",
        "unexpected-unique",
        "missing-unique",
        "sparse",
        "partial",
        "hidden",
        "collation",
    ],
)
def test_incompatible_index_stops_before_any_write(
    prepared_migration: LegacyPhotoMigration,
    case: tuple[str, str, list[tuple[str, int]], dict],
) -> None:
    collection, name, keys, options = case
    target = prepared_migration.sources.database[collection]
    target.drop_index(name)
    target.create_index(keys, name=name, **options)
    assert_rejected_without_writes(prepared_migration)


@pytest.mark.parametrize(
    "revision",
    [True, False, None, 0.0, "0"],
    ids=["true", "false", "null", "float", "text"],
)
def test_invalid_lock_stops_before_any_write(
    prepared_migration: LegacyPhotoMigration, revision: object
) -> None:
    prepared_migration.sources.database["mediaLocks"].update_one(
        {"_id": "writes"}, {"$set": {"revision": revision}}
    )
    assert_rejected_without_writes(prepared_migration)


@pytest.mark.parametrize(
    "revision", [0, 1, Int64(7)], ids=["zero", "positive", "int64"]
)
def test_prepared_definitions_and_integer_lock_allow_apply(
    prepared_migration: LegacyPhotoMigration, revision: int
) -> None:
    database = prepared_migration.sources.database
    database["mediaLocks"].update_one(
        {"_id": "writes"}, {"$set": {"revision": revision}}
    )
    before = database_state(database)
    assert_apply_ready(database)
    assert database_state(database) == before
    candidate = tuple(prepared_migration.plan_batch(BackfillRequest()))[0]
    applied = prepared_migration.apply(candidate)
    assert applied.outcome == "created"
    assert database["mediaFiles"].count_documents({}) == 1
    assert database["media"].count_documents({}) == 1
