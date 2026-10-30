import io
from collections.abc import Callable

import attr
import pytest
from PIL import Image
from pymongo.database import Database

from ebl.media.application.backfill_plan import (
    BackfillPolicy,
    PlannedPhoto,
    SourceRejected,
)
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_candidates import candidate_media
from ebl.media.infrastructure.backfill_images import inspect_image, source_content
from ebl.tests.media.backfill.conftest import image_bytes


@pytest.mark.parametrize(
    "options",
    [
        {"generate_previews": "false"},
        {"map_attribution": "true"},
        {"max_file_size": 0},
        {"max_file_size": True},
        {"max_pixels": 0},
        {"max_pixels": True},
    ],
)
def test_policy_rejects_invalid_bounds(options: dict) -> None:
    with pytest.raises(ValueError):
        BackfillPolicy(**options)


def test_policy_rejects_implicit_primary_changes() -> None:
    with pytest.raises(ValueError, match="primary"):
        BackfillPolicy.of(dict(BackfillPolicy().document(), primaryPolicy="replace"))


def test_policy_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        BackfillPolicy.of({"primaryPolicy": "preserve"})


@pytest.mark.parametrize("declared_length", [0, 1, 10_000])
def test_source_length_must_match_actual_bytes(
    database: Database, legacy_photo: Callable, declared_length: int
) -> None:
    document = legacy_photo()
    with pytest.raises(SourceRejected):
        with source_content(
            database, dict(document, length=declared_length), BackfillPolicy()
        ):
            pass


@pytest.mark.parametrize("pixel_limit", [10, 100])
def test_pillow_safety_limits_become_review(
    pixel_limit: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", pixel_limit)
    content = image_bytes("PNG")
    with pytest.raises(SourceRejected) as rejected:
        inspect_image(io.BytesIO(content), len(content), BackfillPolicy())
    assert rejected.value.outcome == "review"


def test_png_original_is_inspected_without_conversion() -> None:
    content = image_bytes("PNG")
    representation, evidence = inspect_image(
        io.BytesIO(content), len(content), BackfillPolicy()
    )
    assert representation.mime_type == "image/png"
    assert evidence == {}


def test_unmapped_candidate_cannot_become_media() -> None:
    with pytest.raises(ValueError, match="inspected"):
        candidate_media(PlannedPhoto("source", "snapshot", "file", None, "blocked"))


def test_non_string_source_identity_is_never_adopted(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo(file_id=10)
    result = tuple(migration_factory().plan_batch(BackfillRequest()))[0]
    assert result.reason == "unsupported-source-id-type"


def test_missing_filename_is_reported(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    document = legacy_photo()
    database["photos.files"].update_one(
        {"_id": document["_id"]}, {"$unset": {"filename": ""}}
    )
    result = tuple(migration_factory().plan_batch(BackfillRequest()))[0]
    assert result.reason == "missing-filename"


def test_missing_filename_index_does_not_trigger_implicit_creation(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    database["photos.files"].drop_indexes()
    with pytest.raises(ValueError, match="index"):
        tuple(migration_factory().plan_batch(BackfillRequest()))


def test_rejected_planning_request_never_applies(migration_factory: Callable) -> None:
    with pytest.raises(ValueError, match="dry-run"):
        tuple(migration_factory().plan_batch(BackfillRequest(dry_run=False)))


def test_removed_and_changed_metadata_are_conflicts(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    document = legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    database["photos.files"].delete_one({"_id": document["_id"]})
    applied = migration.apply(candidate)
    assert applied.reason == "source-removed"
    database["photos.files"].insert_one(dict(document, extraMetadata="changed"))
    applied = migration.apply(candidate)
    assert applied.reason == "source-changed-since-plan"


def test_changed_metadata_during_read_is_conflict(
    legacy_photo: Callable, migration_factory: Callable, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy_photo()
    migration = migration_factory()
    monkeypatch.setattr(migration.sources, "unchanged", lambda _document: False)
    result = tuple(migration.plan_batch(BackfillRequest()))[0]
    assert result.reason == "source-metadata-changed"


def test_invalid_typed_id_in_plan_is_rejected(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    candidate = tuple(migration_factory().plan_batch(BackfillRequest()))[0]
    with pytest.raises(ValueError, match="source identity"):
        candidate_media(attr.evolve(candidate, source_id='{"id": 1}'))
