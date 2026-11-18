from collections.abc import Callable
from pathlib import Path
import pytest
from pymongo.database import Database
from pymongo.errors import AutoReconnect
from ebl.io.media.backfill_commands import MigrationRunOptions, apply_plan, dry_run
from ebl.media.application.backfill_plan import BackfillPolicy
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import MediaId

TARGET = {"database": "test", "endpointSha256": "local"}


@pytest.mark.parametrize("commit_succeeds", [False, True])
def test_ambiguous_write_recovers_without_deleting_current_previews(
    legacy_photo: Callable,
    migration_factory: Callable,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    commit_succeeds: bool,
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=True))
    plan = tmp_path / "plan.jsonl"
    report = tmp_path / "apply.jsonl"
    dry_run(
        migration,
        MigrationRunOptions(plan, TARGET, False, batch_size=100, max_batches=None),
    )
    database = migration.sources.database
    original_create = migration.repository.create

    def interrupted_create(stored: StoredMedia) -> MediaId:
        if commit_succeeds:
            original_create(stored)
        raise AutoReconnect("Simulated uncertain acknowledgement")

    monkeypatch.setattr(migration.repository, "create", interrupted_create)
    with pytest.raises(AutoReconnect):
        apply_plan(
            migration, plan, MigrationRunOptions(report, TARGET, False, limit=None)
        )
    assert database["media.files"].count_documents({}) == 4
    assert database["media"].count_documents({}) == int(commit_succeeds)
    monkeypatch.setattr(migration.repository, "create", original_create)
    result = apply_plan(
        migration, plan, MigrationRunOptions(report, TARGET, True, limit=None)
    )
    assert result["complete"]
    assert database["media.files"].count_documents({}) == 4
    assert database["media"].count_documents({}) == 1
    assert database["photos.files"].count_documents({}) == 1


def test_partial_preview_failure_cleans_only_owned_staged_handles(
    database: Database,
    legacy_photo: Callable,
    migration_factory: Callable,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=True))
    plan = tmp_path / "plan.jsonl"
    report = tmp_path / "apply.jsonl"
    dry_run(
        migration,
        MigrationRunOptions(plan, TARGET, False, batch_size=100, max_batches=None),
    )

    def fail_thumbnail(_request: object) -> None:
        raise OSError("simulated write failure")

    with monkeypatch.context() as temporary:
        temporary.setattr(migration.store, "write_thumbnail", fail_thumbnail)
        with pytest.raises(OSError):
            apply_plan(
                migration, plan, MigrationRunOptions(report, TARGET, False, limit=None)
            )
    assert database["media.files"].count_documents({}) == 0
    assert database["photos.files"].count_documents({}) == 1
    applied_plan = apply_plan(
        migration, plan, MigrationRunOptions(report, TARGET, True, limit=None)
    )
    assert applied_plan["complete"]
    assert database["media.files"].count_documents({}) == 4
