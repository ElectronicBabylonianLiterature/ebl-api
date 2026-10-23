from io import StringIO
from contextlib import redirect_stderr, redirect_stdout
import json
import os
import runpy
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from pymongo.database import Database

from ebl.io.media import backfill


def captured_main(output: StringIO, arguments: list[str]) -> int:
    with redirect_stdout(output), redirect_stderr(output):
        return backfill.main(arguments)


def command(database: Database, operation: str, *options: str) -> list[str]:
    return [operation, "--database", database.name, *options]


def test_real_cli_plan_indexes_apply_and_repeat(
    database: Database,
    legacy_photo: Callable,
    tmp_path: Path,
    command_output: StringIO,
) -> None:
    legacy_photo()
    plan = tmp_path / "plan.jsonl"
    report = tmp_path / "apply.jsonl"
    exit_status = captured_main(
        command_output,
        command(database, "dry-run", "--report", str(plan), "--generate-previews"),
    )
    assert exit_status == 0
    assert json.loads(command_output.getvalue().splitlines()[-1])["counts"] == {
        "candidate": 1
    }
    exit_status = captured_main(
        command_output,
        command(database, "prepare-indexes", "--confirm-database", database.name),
    )
    assert exit_status == 0
    assert json.loads(command_output.getvalue().splitlines()[-1])["indexesPrepared"]
    apply_arguments = command(
        database,
        "apply",
        "--plan",
        str(plan),
        "--report",
        str(report),
        "--confirm-database",
        database.name,
        "--confirm-source-writes-paused",
    )
    exit_status = captured_main(command_output, apply_arguments)
    assert exit_status == 0
    assert json.loads(command_output.getvalue().splitlines()[-1])["counts"] == {
        "created": 1
    }
    exit_status = captured_main(command_output, [*apply_arguments, "--resume"])
    assert exit_status == 0
    assert database["media"].count_documents({}) == 1


def test_module_entrypoint_and_bounded_exit(
    database: Database,
    legacy_photo: Callable,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command_output: StringIO,
) -> None:
    legacy_photo()
    arguments = command(
        database,
        "dry-run",
        "--report",
        str(tmp_path / "plan.jsonl"),
        "--batch-size",
        "1",
        "--max-batches",
        "1",
    )
    monkeypatch.setattr(sys, "argv", ["backfill", *arguments])
    with pytest.raises(SystemExit) as exited:
        with redirect_stdout(command_output), redirect_stderr(command_output):
            runpy.run_path(str(backfill.__file__), run_name="__main__")
    assert exited.value.code == 2
    assert json.loads(command_output.getvalue().splitlines()[-1])["complete"] is False


@pytest.mark.parametrize(
    "arguments",
    [
        ["dry-run", "--database", " ", "--report", "unused"],
        ["dry-run", "--database", "test", "--report", "unused", "--max-batches", "0"],
        [
            "apply",
            "--database",
            "test",
            "--confirm-database",
            "test",
            "--confirm-source-writes-paused",
            "--plan",
            "same",
            "--report",
            "same",
        ],
    ],
)
def test_invalid_cli_arguments_fail_before_connection(
    arguments: list[str], command_output: StringIO
) -> None:
    exit_status = captured_main(command_output, arguments)
    assert exit_status == 1
    assert "ValueError" in command_output.getvalue()


def test_missing_uri_fails_without_credentials_in_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, command_output: StringIO
) -> None:
    monkeypatch.delenv("MEDIA_MISSING_URI", raising=False)
    exit_status = captured_main(
        command_output,
        [
            "dry-run",
            "--database",
            "test",
            "--uri-env",
            "MEDIA_MISSING_URI",
            "--report",
            str(tmp_path / "none"),
        ],
    )
    assert exit_status == 1
    assert "stopped" in command_output.getvalue()
    assert not (tmp_path / "none").exists()


def test_real_connection_failure_reports_no_uri(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, command_output: StringIO
) -> None:
    original_uri = os.environ["MONGODB_URI"]
    monkeypatch.setenv("MEDIA_INVALID_URI", "https://user:secret@invalid")
    exit_status = captured_main(
        command_output,
        [
            "dry-run",
            "--database",
            "test",
            "--uri-env",
            "MEDIA_INVALID_URI",
            "--report",
            str(tmp_path / "none"),
        ],
    )
    assert exit_status == 1
    assert "secret" not in command_output.getvalue()
    assert os.environ["MONGODB_URI"] == original_uri
