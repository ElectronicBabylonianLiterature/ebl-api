import io
import uuid
from collections.abc import Callable

import attr
import pytest

from ebl.media.application.backfill_plan import BackfillPolicy
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
)
from ebl.media.domain import MediaId, MediaRepresentations
from ebl.media.infrastructure.backfill_candidates import candidate_media
from ebl.media.infrastructure.legacy_media_handles import LegacyRepresentationAdoption
from ebl.tests.media.backfill.conftest import image_bytes


def test_changed_source_before_commit_cleans_previews_only(
    legacy_photo: Callable, migration_factory: Callable, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=True))
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    validations = iter([True, False])
    monkeypatch.setattr(
        migration.sources, "unchanged", lambda _document: next(validations)
    )
    applied = migration.apply(candidate)
    assert applied.reason == "source-metadata-changed"
    assert migration.sources.database["media.files"].count_documents({}) == 0
    assert migration.sources.database["photos.files"].count_documents({}) == 1


def test_concurrent_import_cleans_only_losing_previews(
    legacy_photo: Callable, migration_factory: Callable, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=True))
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    create = migration.repository.create

    def competing_import(stored: StoredMedia) -> MediaId:
        competitor = StoredMedia(
            attr.evolve(
                stored.media,
                representations=MediaRepresentations(
                    stored.media.representations.original
                ),
            ),
            StoredMediaRepresentations(stored.representations.original),
        )
        create(competitor)
        return create(stored)

    monkeypatch.setattr(migration.repository, "create", competing_import)
    applied = migration.apply(candidate)
    assert applied.outcome == "already-present"
    assert migration.sources.database["media.files"].count_documents({}) == 0
    assert migration.sources.database["photos.files"].count_documents({}) == 1


def test_reconciliation_requires_acknowledged_media(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    with pytest.raises(ValueError, match="acknowledged"):
        migration.reconcile_staged(candidate, [])


def test_reconciliation_rejects_another_owner_handle(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    migration.apply(candidate)
    stored = migration.repository.find_stored_by_id(candidate_media(candidate).id)
    assert stored is not None
    other = attr.evolve(
        stored.representations.original, media_id=MediaId(str(uuid.uuid4()))
    )
    with pytest.raises(ValueError, match="owner differs"):
        migration.reconcile_staged(candidate, [other])
    assert migration.sources.database["photos.files"].count_documents({}) == 1


def test_reconciliation_follows_source_owner_with_different_media_id(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    document = legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    proposed = candidate_media(candidate)
    existing = attr.evolve(proposed, id=MediaId(str(uuid.uuid4())))
    original = migration.store.adopt_legacy(
        LegacyRepresentationAdoption(
            existing.id, "photos", document["_id"], existing.representations.original
        )
    )
    migration.repository.create(
        StoredMedia(existing, StoredMediaRepresentations(original))
    )
    staged = migration.store.write_display(
        DisplayRepresentationWriteRequest(
            proposed.id, io.BytesIO(image_bytes()), proposed.representations.original
        )
    )
    applied = migration.apply(candidate)
    assert applied.outcome == "already-present"
    migration.reconcile_staged(candidate, [staged])
    assert migration.sources.database["media.files"].count_documents({}) == 0
    assert migration.repository.find_stored_by_id(existing.id) is not None
