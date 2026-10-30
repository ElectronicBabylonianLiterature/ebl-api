from pathlib import Path
from collections.abc import Callable

import pytest

from ebl.io.media.backfill_commands import MigrationRunOptions, apply_plan
from ebl.io.media.backfill_journal import BackfillJournal, json_bytes, read_document
from ebl.io.media.backfill_plan_file import inspect_plan
from ebl.io.media.backfill_plan_validation import validate_plan_photo
from ebl.media.application.media_requests import BackfillRequest
from ebl.tests.media.backfill.test_backfill_journal import HEADER, ROW


@pytest.mark.parametrize(
    "change",
    [
        {"sourceId": 123},
        {"fragmentId": 123},
        {"outcome": "created"},
        {"attributionEvidence": []},
        {"attributionEvidence": {"Artist": 123}},
        {"representation": {"mimeType": "image/jpeg"}},
    ],
)
def test_plan_rejects_malformed_photo_fields(change: dict) -> None:
    with pytest.raises(ValueError):
        validate_plan_photo(dict(ROW, **change))


def test_plan_rejects_missing_optional_field() -> None:
    document = dict(ROW)
    del document["reason"]
    with pytest.raises(ValueError, match="incomplete"):
        validate_plan_photo(document)


def test_journal_rejects_invalid_row_before_writing(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    with BackfillJournal(path, HEADER, False) as journal:
        before = path.read_bytes()
        with pytest.raises(ValueError, match="source identity"):
            journal.append({"kind": "photo", "outcome": "blocked"})
        with pytest.raises(ValueError, match="valid kind"):
            journal.append({"kind": "staged", "sourceId": "source"})
        assert path.read_bytes() == before


def test_non_object_journal_rows_are_rejected() -> None:
    with pytest.raises(ValueError, match="objects"):
        read_document(b"[]")


@pytest.mark.parametrize(
    "header", [dict(HEADER, command="apply"), dict(HEADER, policy=None)]
)
def test_plan_requires_dry_run_target_and_policy(tmp_path: Path, header: dict) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, header, False) as journal:
        journal.finish()
    with pytest.raises(ValueError):
        inspect_plan(path)


def test_unknown_plan_row_kind_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False):
        pass
    with path.open("ab") as stream:
        stream.write(json_bytes({"kind": "unexpected"}))
    with pytest.raises(ValueError, match="unknown row"):
        inspect_plan(path)


def test_entire_plan_is_validated_before_first_database_write(
    legacy_photo: Callable, migration_factory: Callable, tmp_path: Path
) -> None:
    legacy_photo()
    migration = migration_factory()
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    plan = tmp_path / "plan.jsonl"
    with BackfillJournal(plan, HEADER, False) as journal:
        journal.append(candidate.document())
        journal.append(dict(ROW, attributionEvidence=[]))
        journal.finish()
    with pytest.raises(ValueError, match="Attribution evidence"):
        apply_plan(
            migration,
            plan,
            MigrationRunOptions(
                tmp_path / "apply.jsonl",
                {
                    "database": HEADER["database"],
                    "endpointSha256": HEADER["endpointSha256"],
                },
            ),
        )
    assert migration.sources.database["mediaFiles"].count_documents({}) == 0
    assert migration.sources.database["media"].count_documents({}) == 0
