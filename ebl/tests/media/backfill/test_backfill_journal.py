from pathlib import Path

import pytest

from ebl.io.media.backfill_journal import BackfillJournal, json_bytes
from ebl.io.media.backfill_plan_file import inspect_plan, plan_rows
from ebl.media.application.backfill_plan import BackfillPolicy, PlannedPhoto


HEADER = {
    "command": "dry-run",
    "database": "test",
    "endpointSha256": "example",
    "policy": BackfillPolicy().document(),
}
ROW = PlannedPhoto("source", "snapshot", "file", None, "blocked").document()


def test_resume_truncates_only_incomplete_last_row(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False) as journal:
        journal.append(ROW)
    with path.open("ab") as stream:
        stream.write(b'{"outcome":')
    with BackfillJournal(path, HEADER, True) as journal:
        assert journal.last_source == "source"
        assert journal.counts == {"blocked": 1}
        journal.finish()
    header, digest = inspect_plan(path)
    assert header["database"] == "test"
    assert len(digest) == 64
    assert list(plan_rows(path, None)) == [ROW]
    assert list(plan_rows(path, "source")) == []


def test_resume_binds_target_and_command(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False):
        pass
    with pytest.raises(ValueError, match="Resume target"):
        BackfillJournal(path, dict(HEADER, command="apply"), True)
    with pytest.raises(FileExistsError):
        BackfillJournal(path, HEADER, False)


def test_incomplete_plan_is_not_applicable(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False) as journal:
        journal.append(ROW)
    with pytest.raises(ValueError, match="completed dry-run"):
        inspect_plan(path)


def test_completed_journal_cannot_append(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False) as journal:
        journal.finish()
        with pytest.raises(ValueError, match="cannot be extended"):
            journal.append(ROW)
    with BackfillJournal(path, HEADER, True) as journal:
        assert journal.completed
        journal.finish()


def test_checksum_detects_changed_plan(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False) as journal:
        journal.append(ROW)
        journal.finish()
    path.write_bytes(path.read_bytes().replace(b'"blocked"', b'"review"'))
    with pytest.raises(ValueError, match="checksum"):
        inspect_plan(path)
    with pytest.raises(ValueError, match="checksum"):
        BackfillJournal(path, HEADER, True)


def test_extra_rows_and_missing_resume_source_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False) as journal:
        journal.append(ROW)
        journal.finish()
    with pytest.raises(ValueError, match="absent"):
        list(plan_rows(path, "not-in-plan"))
    with path.open("ab") as stream:
        stream.write(json_bytes(ROW))
    with pytest.raises(ValueError, match="trailing"):
        inspect_plan(path)
    with pytest.raises(ValueError, match="after"):
        BackfillJournal(path, HEADER, True)


def test_journal_lock_prevents_simultaneous_writers(tmp_path: Path) -> None:
    path = tmp_path / "plan.jsonl"
    with BackfillJournal(path, HEADER, False):
        with pytest.raises(BlockingIOError):
            BackfillJournal(path, HEADER, True)
