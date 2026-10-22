import argparse
import json
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest

from scripts.maps import import_findspot_map_locations as cli


@pytest.fixture
def arguments(tmp_path: Path) -> argparse.Namespace:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps([{"polygonId": "assur-test"}]))
    mappings = tmp_path / "mappings.json"
    mappings.write_text(
        json.dumps(
            [
                {
                    "findspotId": 1,
                    "polygonIds": ["assur-test"],
                    "locationPrecision": "excavation-area",
                    "matchMethod": "verified-source",
                    "source": "synthetic fixture",
                    "sourceRevision": "test",
                }
            ]
        )
    )
    return cli._parse_args(
        [
            "--dry-run",
            "--allow-approved-development-target",
            "--confirm-database",
            "ebldev",
            "--mappings",
            str(mappings),
            "--inventory",
            str(inventory),
        ]
    )


@pytest.mark.parametrize("include_previous", [False, True])
def test_approved_target_receives_validated_mapping_inputs(
    arguments: argparse.Namespace,
    include_previous: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if include_previous:
        arguments.previous_mappings = arguments.mappings
        arguments.previous_inventory = arguments.inventory
    verify_target = Mock()
    monkeypatch.setattr(cli, "validate_approved_development_target", verify_target)
    database = object()

    assert (
        cli._verify_approved_development_target(
            "mongodb://example.invalid/ebldev", database, arguments
        )
        is None
    )

    verify_target.assert_called_once()
    assert verify_target.call_args.args[:3] == (
        "mongodb://example.invalid/ebldev",
        database,
        "ebldev",
    )
    inputs = verify_target.call_args.args[3]
    assert len(inputs.records) == 1
    assert inputs.polygon_ids == {"assur-test"}
    assert len(inputs.previous_records) == int(include_previous)
    stdout, _ = cast(tuple[str, str], capsys.readouterr())
    assert "Approved development target verified" in stdout


@pytest.mark.parametrize(
    "invalid_input,exit_code,message",
    [
        ("current", 1, "mapping input is invalid"),
        ("previous", 1, "previous mapping input is invalid"),
        ("missing_previous_inventory", 2, "--previous-inventory is required"),
    ],
)
def test_invalid_mapping_inputs_refuse_approved_target(
    arguments: argparse.Namespace,
    invalid_input: str,
    exit_code: int,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    invalid_mappings = tmp_path / "invalid.json"
    invalid_mappings.write_text('[{"findspotId": 1}]')
    if invalid_input == "current":
        arguments.mappings = invalid_mappings
    else:
        arguments.previous_mappings = invalid_mappings
        if invalid_input == "previous":
            arguments.previous_inventory = arguments.inventory
    verify_target = Mock()
    monkeypatch.setattr(cli, "validate_approved_development_target", verify_target)

    assert (
        cli._verify_approved_development_target(
            "mongodb://example.invalid/ebldev", object(), arguments
        )
        == exit_code
    )

    _, stderr = cast(tuple[str, str], capsys.readouterr())
    assert message in stderr
    verify_target.assert_not_called()


def test_failed_target_fingerprint_is_reported_as_refusal(
    arguments: argparse.Namespace,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli,
        "validate_approved_development_target",
        Mock(side_effect=ValueError("fingerprint mismatch")),
    )

    assert (
        cli._verify_approved_development_target(
            "mongodb://example.invalid/ebldev", object(), arguments
        )
        == 2
    )

    _, stderr = cast(tuple[str, str], capsys.readouterr())
    assert "fingerprint mismatch" in stderr
