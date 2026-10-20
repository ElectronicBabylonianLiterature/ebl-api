import json
import runpy
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from ebl.tests.provenance.kmz_test_helpers import (
    POINT,
    POINT_XML,
    POLYGON_XML,
    placemark,
    record,
    write_kml,
)
from scripts import import_kmz_coordinates as cli


def collection_stub() -> Mock:
    collection = Mock()
    collection.find.return_value = [
        {"_id": "ASSUR", "longName": "Assur", "abbreviation": "Ass"}
    ]
    collection.update_one.return_value.matched_count = 1
    collection.update_one.return_value.modified_count = 1
    return collection


def test_dry_run_apply_and_write_filters(tmp_path: Path) -> None:
    collection = collection_stub()
    path = write_kml(tmp_path / "source.kml")
    report = cli.run_import(collection, path)
    collection.update_one.assert_not_called()
    assert report["apply"]["databaseWritesPerformed"] == 0
    applied = cli.run_import(collection, path, apply_requested=True)
    assert applied["apply"]["databaseWritesPerformed"] == 1
    update_filter, update = collection.update_one.call_args.args
    assert update_filter["_id"] == "ASSUR"
    assert len(update_filter["$and"]) == 2
    assert update["$set"]["coordinates"] == POINT
    assert len(update["$set"]["polygonCoordinates"]) == 3


def test_allowlist_exclusions_never_write() -> None:
    collection = collection_stub()
    proposal = cli.build_import_plan((record(),), (placemark(),)).proposed_updates
    result = cli.apply_proposed_updates(collection, proposal, {})
    assert result[0]["skippedReason"] == "not in allowlist"
    collection.update_one.assert_not_called()
    result = cli.apply_proposed_updates(collection, proposal)
    assert result[0]["modifiedCount"] == 1
    update_filter, update = collection.update_one.call_args.args
    assert "$and" not in update_filter
    assert update == {"$set": {"coordinates": POINT}}


def test_text_report_includes_candidates_and_empty_updates() -> None:
    records = (record(), record("Urúk", "URUK"), record("Missing", "MISSING"))
    marks = (
        placemark(geometry=POINT_XML + POLYGON_XML),
        placemark("Uruk"),
        placemark("Uruk"),
    )
    parsed = cli.KmlParseResult("memory", "doc.kml", marks)
    plan = cli.build_import_plan(records, marks[:2])
    report = cli.build_report(records, parsed, plan)
    buffer = StringIO()
    with redirect_stdout(buffer):
        cli.print_text_report(report)
    output = buffer.getvalue()
    assert "polygon coordinate count: 3" in output
    assert "Normalized review candidates:" in output
    assert "no match: 1" in output
    empty = cli.build_report((), parsed, cli.build_import_plan((), ()))
    with redirect_stdout(buffer):
        cli.print_text_report(empty)
    assert "  none" in buffer.getvalue()


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_uses_selected_database_and_closes_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    json_output: bool,
) -> None:
    collection = collection_stub()
    client = Mock()
    client.get_database.return_value = {"provenances": collection}
    constructor = Mock(return_value=client)
    monkeypatch.setattr(cli, "MongoClient", constructor)
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid")
    arguments = ["--kmz", str(write_kml(tmp_path / "source.kml")), "--database", "test"]
    if json_output:
        arguments.append("--json")
    buffer = StringIO()
    with redirect_stdout(buffer):
        assert cli.main(arguments) == 0
    client.get_database.assert_called_once_with("test")
    client.close.assert_called_once_with()
    output = buffer.getvalue()
    if json_output:
        assert json.loads(output)["apply"]["requested"] is False
    else:
        assert "Mode: DRY RUN" in output
    collection.update_one.assert_not_called()


def test_script_missing_uri_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.setattr(
        sys, "argv", ["import_kmz_coordinates.py", "--kmz", "unused.kml"]
    )
    buffer = StringIO()
    with redirect_stderr(buffer):
        assert cli.main(["--kmz", "unused.kml"]) == 2
        with pytest.raises(SystemExit) as error:
            runpy.run_path("scripts/import_kmz_coordinates.py", run_name="__main__")
    assert error.value.code == 2
    assert "MONGODB_URI is required" in buffer.getvalue()
