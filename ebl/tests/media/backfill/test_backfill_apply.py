from collections.abc import Callable

import attr
from bson.binary import Binary
from gridfs import GridFS
from pymongo.database import Database

from ebl.media.infrastructure.backfill_candidates import candidate_media
from ebl.media.application.backfill_plan import BackfillPolicy
from ebl.media.application.media_requests import BackfillRequest


def test_apply_is_idempotent_and_protects_original(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    document = legacy_photo()
    original = GridFS(database, "photos").get(document["_id"]).read()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    applied = migration.apply(candidate)
    assert applied.outcome == "created"
    applied = migration.apply(candidate)
    assert applied.outcome == "already-present"
    media = candidate_media(candidate)
    stored = migration.repository.find_stored_by_id(media.id)
    assert stored is not None
    assert not stored.media.associations[0].is_primary
    migration.store.delete_representation(stored.representations.original)
    assert GridFS(database, "photos").get(document["_id"]).read() == original
    assert database["media"].count_documents({}) == 1


def test_same_length_chunk_change_conflicts(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    document = legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    chunk = database["photos.chunks"].find_one({"files_id": document["_id"]})
    assert chunk is not None
    data = bytearray(chunk["data"])
    data[-10] ^= 1
    database["photos.chunks"].update_one(
        {"_id": chunk["_id"]}, {"$set": {"data": Binary(data)}}
    )
    result = migration.apply(candidate)
    assert result.outcome == "conflicting"
    assert database["media"].count_documents({}) == 0


def test_source_mapping_change_conflicts(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    legacy_photo()
    applied = migration.apply(candidate)
    assert applied.outcome == "conflicting"


def test_preview_generation_uses_owned_files(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=True))
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    applied = migration.apply(candidate)
    assert applied.outcome == "created"
    stored = migration.repository.find_stored_by_id(candidate_media(candidate).id)
    assert stored is not None
    assert stored.representations.display is not None
    assert len(stored.representations.thumbnails) == 3
    assert database["media.files"].count_documents({}) == 4
    assert database["thumbnails.files"].count_documents({}) == 0
    applied = migration.apply(candidate)
    assert applied.outcome == "already-present"
    assert database["media.files"].count_documents({}) == 4


def test_changed_existing_record_is_not_overwritten(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    migration.apply(candidate)
    stored = migration.repository.find_stored_by_id(candidate_media(candidate).id)
    assert stored is not None
    changed = attr.evolve(
        stored, media=attr.evolve(stored.media, original_filename="K.2.jpg")
    )
    migration.repository.replace(changed)
    applied = migration.apply(candidate)
    assert applied.outcome == "conflicting"
    assert migration.repository.find_stored_by_id(stored.media.id) == changed
