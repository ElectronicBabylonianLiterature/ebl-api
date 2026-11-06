import hashlib
import io
import json
from pathlib import Path
import tarfile

import pytest

from ebl.fragmentarium.application.map_artifact_generator import DEFAULT_OUTPUT_DIR
from scripts.maps import frontend_transfer_archive as transfer
from scripts.maps.frontend_transfer_contract import (
    CONTRACT_VERSION,
    TransferProvenance,
    build_contract_manifest,
    transfer_names,
)
from scripts.maps.frontend_transfer_manifest import read_artifact_sets
from ebl.tests.fragmentarium.frontend_transfer_test_helpers import (
    copy_artifacts,
    replace_declared_file,
)


def test_contract_is_content_addressed_and_independent_of_frontend_commits() -> None:
    contents, revisions = read_artifact_sets(DEFAULT_OUTPUT_DIR)
    first = json.loads(
        build_contract_manifest(
            contents, revisions, TransferProvenance("a" * 40, False)
        )
    )
    second = json.loads(
        build_contract_manifest(contents, revisions, TransferProvenance("b" * 40, True))
    )
    assert first["contractVersion"] == CONTRACT_VERSION
    assert first["schemaVersion"] == 1
    assert first["geometryIncluded"] is False
    assert first["contractRevision"] == second["contractRevision"]
    assert first["producer"] != second["producer"]
    assert set(first["fileChecksums"]) == set(transfer_names())
    for name, checksum in first["fileChecksums"].items():
        assert checksum == hashlib.sha256(contents[name]).hexdigest()
    payload = {
        key: value
        for key, value in first.items()
        if key not in {"producer", "contractRevision"}
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    assert (
        first["contractRevision"]
        == "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    )
    assert "frontendGeneratorCommit" not in first
    assert set(first["sites"]) == {"ASSUR", "KALHU", "NIPPUR", "URUK"}
    assert sum(site["polygonCount"] for site in first["sites"].values()) == 294


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../escape",
        "dir/file",
        "..\\escape",
        "C:escape",
        "line\nfile",
        "bad\x7fname",
    ],
)
def test_archive_paths_are_safe_across_platforms(name: str) -> None:
    with tarfile.open(fileobj=io.BytesIO(), mode="w") as archive:
        with pytest.raises(ValueError, match="must be a basename"):
            transfer._add_member(archive, name, b"payload")


def test_archive_includes_verifiable_machine_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(transfer, "_git", lambda *args: "# branch.oid " + "a" * 40)
    output = transfer.build_archive(DEFAULT_OUTPUT_DIR, tmp_path / "transfer.tar.gz")
    with tarfile.open(output, "r:gz") as archive:
        manifest = archive.extractfile("ARTIFACT_MANIFEST.json")
        assert manifest is not None
        payload = json.loads(manifest.read())
        assert len(archive.getmembers()) == 10
        assert not any(name.endswith(".geojson") for name in archive.getnames())
        for name, checksum in payload["fileChecksums"].items():
            member = archive.extractfile(name)
            assert member is not None
            assert hashlib.sha256(member.read()).hexdigest() == checksum


def test_text_and_json_share_one_git_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, ...]] = []

    def changing_git(*arguments: str) -> str:
        calls.append(arguments)
        return "# branch.oid " + ("a" if len(calls) == 1 else "b") * 40

    monkeypatch.setattr(transfer, "_git", changing_git)
    output = transfer.build_archive(DEFAULT_OUTPUT_DIR, tmp_path / "snapshot.tar.gz")
    with tarfile.open(output, "r:gz") as archive:
        text = archive.extractfile(transfer.ARCHIVE_MANIFEST)
        machine = archive.extractfile("ARTIFACT_MANIFEST.json")
        assert text is not None and machine is not None
        payload = json.loads(machine.read())
        assert f"commit: {payload['producer']['commit']}\n" in text.read().decode()
    assert calls == [
        ("status", "--porcelain=v2", "--branch", "--untracked-files=normal")
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("derivationStatus", "invented"),
        ("membershipStatus", {}),
        ("candidatePolygonIds", ["unknown"]),
        ("sourceRows", []),
        ("sourceRows", [{"findspotId": True}]),
        ("sourceRows", [{"findspotId": 1}]),
    ],
)
def test_malformed_curation_context_is_rejected(
    tmp_path: Path, field: str, value: object
) -> None:
    data_dir = copy_artifacts(tmp_path)
    name = "assur_findspot_polygon_curation_template.json"
    rows = json.loads((data_dir / name).read_text())
    rows[0][field] = value
    replace_declared_file(data_dir, name, rows)
    with pytest.raises(ValueError, match="Invalid curation context"):
        transfer.build_archive(data_dir, tmp_path / "invalid.tar.gz")


def test_transfer_rejects_inexact_javascript_identity(tmp_path: Path) -> None:
    data_dir = copy_artifacts(tmp_path)
    name = "assur_findspot_polygon_mappings.json"
    rows = json.loads((data_dir / name).read_text())
    rows[0]["findspotId"] = 2**53
    replace_declared_file(data_dir, name, rows)
    with pytest.raises(ValueError, match="Invalid mapping identity"):
        transfer.build_archive(data_dir, tmp_path / "inexact.tar.gz")


def test_archive_rejects_cross_site_findspot_ids(tmp_path: Path) -> None:
    data_dir = copy_artifacts(tmp_path)
    name = "kalhu_findspot_polygon_curation_template.json"
    records = json.loads((data_dir / name).read_text())
    assur_mappings = data_dir / "assur_findspot_polygon_mappings.json"
    findspot_id = json.loads(assur_mappings.read_text())[0]["findspotId"]
    records[0]["findspotId"] = findspot_id
    for source_row in records[0]["sourceRows"]:
        source_row["findspotId"] = findspot_id
    replace_declared_file(data_dir, name, records)
    with pytest.raises(ValueError, match="Findspot IDs must be unique across sites"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")
