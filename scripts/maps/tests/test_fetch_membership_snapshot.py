import hashlib
from io import BytesIO
import json
from pathlib import Path
import runpy
import sys
from urllib.request import Request

import pytest

from scripts.maps import fetch_membership_snapshot as snapshot
from scripts.maps.map_membership import load_membership_evidence

RAW_RESPONSE = json.dumps(
    [
        {"_id": 2, "site": "Aššur", "area": "discarded"},
        {"_id": 1, "site": "Umma"},
        {"_id": 1, "site": None},
    ],
    ensure_ascii=False,
).encode("utf-8")
FETCHED_AT = "2026-11-06T06:09:41.686Z"


def test_snapshot_preserves_ambiguous_membership_and_response_checksum() -> None:
    result = snapshot.build_membership_snapshot(RAW_RESPONSE, FETCHED_AT, '"etag"')

    assert result == {
        "schemaVersion": 1,
        "source": snapshot.SOURCE_URL,
        "sourceRevision": "sha256:" + hashlib.sha256(RAW_RESPONSE).hexdigest(),
        "fetchedAt": FETCHED_AT,
        "etag": '"etag"',
        "findspots": [
            {"findspotId": 1, "siteName": None},
            {"findspotId": 1, "siteName": "Umma"},
            {"findspotId": 2, "siteName": "Aššur"},
        ],
    }


@pytest.mark.parametrize(
    "response,message",
    [
        ({}, "JSON array"),
        ([None], "_id and site"),
        ([{"_id": 1}], "_id and site"),
        ([{"_id": True, "site": None}], "BSON int64"),
        ([{"_id": 2**63, "site": None}], "BSON int64"),
        ([{"_id": 1, "site": " "}], "nonblank strings"),
        ([{"_id": 1, "site": 1}], "nonblank strings"),
    ],
)
def test_snapshot_rejects_invalid_source_records(
    response: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        snapshot.build_membership_snapshot(json.dumps(response).encode(), FETCHED_AT)


def test_snapshot_replay_is_byte_reproducible_and_accepted_by_loader(
    tmp_path: Path,
) -> None:
    response = tmp_path / "response.json"
    response.write_bytes(RAW_RESPONSE)
    output = tmp_path / "snapshot.json"
    arguments = [
        "--response-file",
        str(response),
        "--output",
        str(output),
        "--fetched-at",
        FETCHED_AT,
        "--etag",
        '"fixture"',
    ]

    assert snapshot.main(arguments) == 0
    first = output.read_bytes()
    assert snapshot.main(arguments) == 0
    assert output.read_bytes() == first
    evidence = load_membership_evidence(output)
    assert evidence.findspot_ids_for("Aššur") == frozenset({2})
    assert evidence.findspot_ids_for("Umma") == frozenset()


def test_snapshot_fetch_uses_canonical_url_and_preserves_etag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ApiResponse(BytesIO):
        headers = {"ETag": '"fixture"'}

    def open_response(request: Request, timeout: int) -> ApiResponse:
        assert request.full_url == snapshot.SOURCE_URL
        assert request.get_header("Accept") == "application/json"
        assert timeout == 30
        return ApiResponse(RAW_RESPONSE)

    monkeypatch.setattr(snapshot, "urlopen", open_response)

    assert snapshot.fetch_response() == (RAW_RESPONSE, '"fixture"')


def test_snapshot_cli_fetches_and_supplies_timestamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(snapshot, "fetch_response", lambda: (RAW_RESPONSE, None))
    output = tmp_path / "nested" / "snapshot.json"

    assert snapshot.main(["--output", str(output)]) == 0
    assert json.loads(output.read_text())["fetchedAt"].endswith("Z")


def test_snapshot_cli_reports_errors_without_overwriting_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    response, output = tmp_path / "response.json", tmp_path / "snapshot.json"
    response.write_text("{}")
    output.write_text("existing snapshot")

    assert (
        snapshot.main(["--response-file", str(response), "--output", str(output)]) == 2
    )
    assert capsys.readouterr()[1].startswith("error: Canonical findspot response")
    assert output.read_text() == "existing snapshot"


def test_snapshot_module_executes_main_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = tmp_path / "response.json"
    response.write_bytes(RAW_RESPONSE)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "snapshot",
            "--response-file",
            str(response),
            "--output",
            str(tmp_path / "out.json"),
        ],
    )

    with pytest.raises(SystemExit) as result:
        runpy.run_module("scripts.maps.fetch_membership_snapshot", run_name="__main__")

    assert result.value.code == 0
