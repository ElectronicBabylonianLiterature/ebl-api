import json
import runpy
from dataclasses import replace
from unittest.mock import Mock

import pytest

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    ImportIssue,
    ImportSummary,
)
from scripts.maps import import_findspot_map_locations as cli


def _summary(issues: tuple[ImportIssue, ...] = ()) -> ImportSummary:
    return ImportSummary(
        scanned=1,
        valid=1 if not issues else 0,
        invalid=len(issues),
        unknown_findspots=0,
        wrong_site=0,
        unknown_polygons=0,
        existing=0,
        new=1,
        changed=0,
        skipped=0,
        applied=0,
        dry_run=True,
        rollback=False,
        issues=issues,
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Mock:
    database_client = Mock()
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost/ebl-cli-test")
    monkeypatch.setenv("MONGODB_DB", "ebl-cli-test")
    monkeypatch.setattr(cli, "MongoClient", Mock(return_value=database_client))
    return database_client


@pytest.mark.parametrize(
    "arguments",
    [
        ["--apply", "--dry-run"],
        ["--dry-run", "--apply"],
        ["--rollback", "--dry-run"],
        ["--dry-run", "--rollback"],
    ],
)
def test_conflicting_modes_fail_before_connecting(
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    client_factory = Mock(side_effect=AssertionError("Database connection attempted"))
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost/ebl-cli-test")
    monkeypatch.setattr(cli, "MongoClient", client_factory)

    with pytest.raises(SystemExit) as error:
        cli.main(arguments)

    assert error.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err
    client_factory.assert_not_called()


@pytest.mark.parametrize(
    "arguments,dry_run,rollback",
    [
        ([], True, False),
        (["--dry-run"], True, False),
        (["--apply"], False, False),
        (["--rollback"], False, True),
    ],
)
def test_single_modes_preserve_import_behavior(
    arguments: list[str],
    dry_run: bool,
    rollback: bool,
    monkeypatch: pytest.MonkeyPatch,
    client: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = replace(_summary(), dry_run=dry_run, rollback=rollback)
    importer = Mock(return_value=summary)
    monkeypatch.setattr(cli, "run_import", importer)

    assert cli.main(arguments) == 0

    client.get_database.assert_called_once_with("ebl-cli-test")
    importer.assert_called_once_with(
        client.get_database.return_value,
        cli.ImportPaths(),
        dry_run=dry_run,
        rollback=rollback,
    )
    assert "Applied: 0" in capsys.readouterr().out
    client.close.assert_called_once_with()


def test_invalid_import_returns_failure_with_json_report(
    monkeypatch: pytest.MonkeyPatch,
    client: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = _summary((ImportIssue(1, "unknown polygon"),))
    monkeypatch.setattr(cli, "run_import", Mock(return_value=summary))

    assert cli.main(["--json"]) == 1

    report = json.loads(capsys.readouterr().out)
    assert report["invalid"] == 1
    assert report["issues"] == [{"findspot_id": 1, "reason": "unknown polygon"}]
    client.close.assert_called_once_with()


@pytest.mark.parametrize("issue_count", [1, 11])
def test_text_report_limits_issue_details(
    issue_count: int, capsys: pytest.CaptureFixture[str]
) -> None:
    cli._print_summary(
        _summary(
            tuple(ImportIssue(index, "unknown polygon") for index in range(issue_count))
        )
    )

    output = capsys.readouterr().out
    assert output.count("unknown polygon") == min(issue_count, 10)
    assert ("and 1 more" in output) is (issue_count > 10)


def test_entrypoint_refuses_missing_database_uri(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.setattr("sys.argv", [cli.__file__])

    with pytest.raises(SystemExit) as error:
        runpy.run_path(cli.__file__, run_name="__main__")

    assert error.value.code == 2
    assert "Refusing to run unless MONGODB_URI" in capsys.readouterr().err


def test_refused_target_closes_client_without_importing(
    monkeypatch: pytest.MonkeyPatch,
    client: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid/ebl-cli-test")
    importer = Mock()
    monkeypatch.setattr(cli, "run_import", importer)

    assert cli.main(["--dry-run"]) == 2

    assert "without approved development mode" in capsys.readouterr().err
    importer.assert_not_called()
    client.close.assert_called_once_with()
