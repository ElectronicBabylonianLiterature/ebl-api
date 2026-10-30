import argparse
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlunsplit
import pytest
from ebl.io.media.backfill import parser, target_identity, validate_arguments
from ebl.io.media.backfill_commands import MigrationRunOptions, apply_plan, dry_run
from ebl.media.application.backfill_plan import BackfillPolicy

TARGET = {"database": "test", "endpointSha256": "local"}


def test_plan_then_apply_resume(
    legacy_photo: Callable, migration_factory: Callable, tmp_path: Path
) -> None:
    legacy_photo()
    legacy_photo("K.2.jpg", create_fragment=False)
    migration = migration_factory()
    plan = tmp_path / "plan.jsonl"
    report = tmp_path / "apply.jsonl"
    first = dry_run(
        migration, MigrationRunOptions(plan, TARGET, False, batch_size=1, max_batches=1)
    )
    assert first["complete"] is False
    completed = dry_run(
        migration,
        MigrationRunOptions(plan, TARGET, True, batch_size=1, max_batches=None),
    )
    assert completed == {"complete": True, "counts": {"candidate": 1, "blocked": 1}}
    applied_plan = apply_plan(
        migration, plan, MigrationRunOptions(report, TARGET, False, limit=1)
    )
    assert applied_plan["complete"] is False
    applied_plan = apply_plan(
        migration, plan, MigrationRunOptions(report, TARGET, True, limit=None)
    )
    assert applied_plan == {
        "complete": True,
        "counts": {"created": 1, "blocked": 1},
        "pendingSources": [],
    }
    applied_plan = apply_plan(
        migration, plan, MigrationRunOptions(report, TARGET, True, limit=None)
    )
    assert applied_plan["complete"] is True


def test_apply_target_and_policy_must_match(
    legacy_photo: Callable, migration_factory: Callable, tmp_path: Path
) -> None:
    legacy_photo()
    migration = migration_factory()
    plan = tmp_path / "plan.jsonl"
    report = tmp_path / "apply.jsonl"
    dry_run(
        migration,
        MigrationRunOptions(plan, TARGET, False, batch_size=100, max_batches=None),
    )
    with pytest.raises(ValueError, match="another database"):
        apply_plan(
            migration,
            plan,
            MigrationRunOptions(
                report, dict(TARGET, database="different"), False, limit=None
            ),
        )
    different = migration_factory(BackfillPolicy(map_attribution=False))
    with pytest.raises(ValueError, match="policy"):
        apply_plan(
            different, plan, MigrationRunOptions(report, TARGET, False, limit=None)
        )
    assert not report.exists()


def test_explicit_target_and_confirmation() -> None:
    arguments = parser().parse_args(
        ["dry-run", "--database", "ebltest", "--report", "report.jsonl"]
    )
    validate_arguments(arguments)
    assert arguments.command == "dry-run"
    with pytest.raises(SystemExit):
        parser().parse_args(["apply", "--database", "ebl"])
    with pytest.raises(ValueError, match="confirmation"):
        validate_arguments(
            argparse.Namespace(
                command="prepare-indexes", database="ebl", confirm_database="ebldev"
            )
        )


@pytest.mark.parametrize(
    "username,password",
    [("test-user", "test-password"), ("other-test-user", "other-test-password")],
)
def test_uri_credentials_are_not_in_target(username: str, password: str) -> None:
    # Assemble synthetic credentials for this parser-only test; no connection is made.
    uri = urlunsplit(("mongodb", f"{username}:{password}@localhost:27017", "", "", ""))
    assert target_identity(uri, "ebl") == target_identity(
        "mongodb://localhost:27017", "ebl"
    )


def test_target_requires_explicit_endpoint() -> None:
    with pytest.raises(ValueError, match="explicit endpoint"):
        target_identity("not-mongodb", "ebl")
