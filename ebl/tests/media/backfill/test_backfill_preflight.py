from collections.abc import Callable

import pytest
from pymongo.database import Database
from pymongo.read_preferences import ReadPreference

from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_preflight import (
    assert_apply_ready,
    prepare_legacy_indexes,
)
from ebl.media.infrastructure.backfill_sources import LegacyPhotoSources


def test_index_preparation_requires_existing_legacy_database(
    database: Database,
) -> None:
    with pytest.raises(ValueError, match="legacy fragments and photos"):
        prepare_legacy_indexes(database)


def test_explicit_index_preparation_creates_filename_index(
    database: Database, legacy_photo: Callable
) -> None:
    legacy_photo()
    database["photos.files"].drop_indexes()
    prepare_legacy_indexes(database)
    assert (
        LegacyPhotoSources(database).filename_index() == "media_legacy_photo_filename"
    )


def test_apply_without_indexes_cannot_register_legacy_handle(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory(initialize=False)
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    before = set(database.list_collection_names())
    with pytest.raises(ValueError, match="prepare-indexes"):
        migration.apply(candidate)
    assert set(database.list_collection_names()) == before


def test_apply_without_lock_cannot_register_legacy_handle(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    database["mediaLocks"].delete_one({"_id": "writes"})
    with pytest.raises(ValueError, match="coordination"):
        migration.apply(candidate)
    assert database["mediaFiles"].count_documents({}) == 0


def test_ready_preflight_is_read_only(migration_factory: Callable) -> None:
    migration = migration_factory()
    before = migration.sources.database["mediaLocks"].find_one({"_id": "writes"})
    assert_apply_ready(migration.sources.database)
    assert (
        migration.sources.database["mediaLocks"].find_one({"_id": "writes"}) == before
    )


def test_source_revalidation_forces_primary_reads(database: Database) -> None:
    sources = LegacyPhotoSources(
        database.with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
    )
    assert sources.database.read_preference == ReadPreference.PRIMARY
    assert sources.files.read_preference == ReadPreference.PRIMARY
