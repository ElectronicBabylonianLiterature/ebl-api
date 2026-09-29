import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile

from marshmallow import ValidationError
import pytest

from ebl.common.query.parameter_parser import MAX_FINDSPOT_ID
from ebl.fragmentarium.application.map_artifact_generator import DEFAULT_OUTPUT_DIR
from scripts.maps import frontend_transfer_archive as transfer

EXPECTED_MEMBERS = (
    "ARTIFACT_MANIFEST.txt",
    "assur_polygon_inventory.json",
    "assur_findspot_polygon_mappings.json",
    "uruk_polygon_inventory.json",
    "uruk_findspot_polygon_mappings.json",
    "kalhu_polygon_inventory.json",
    "kalhu_findspot_polygon_mappings.json",
    "nippur_polygon_inventory.json",
    "nippur_findspot_polygon_mappings.json",
)


@pytest.fixture(autouse=True)
def stable_git_provenance(monkeypatch):
    def fake_git(*args: str) -> str:
        if args[0] == "status":
            return ""
        if "--abbrev-ref" in args:
            return "map/backend-06-artifact-transfer"
        return "a" * 40

    monkeypatch.setattr(transfer, "_git", fake_git)


def _copy_artifacts(tmp_path: Path) -> Path:
    destination = tmp_path / "artifacts"
    shutil.copytree(DEFAULT_OUTPUT_DIR, destination)
    return destination


def _directory_snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def _replace_declared_file(data_dir: Path, name: str, content: bytes) -> None:
    (data_dir / name).write_bytes(content)
    manifest_path = data_dir / f"{name.split('_', 1)[0]}_artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name] = hashlib.sha256(content).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def test_build_archive_is_deterministic_normalized_and_documents_geometry(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    before = _directory_snapshot(data_dir)
    first = transfer.build_archive(data_dir, tmp_path / "one" / "transfer.tar.gz")
    second = transfer.build_archive(data_dir, tmp_path / "two" / "transfer.tar.gz")

    assert first.read_bytes() == second.read_bytes()
    assert _directory_snapshot(data_dir) == before
    with tarfile.open(first, "r:gz") as archive:
        assert tuple(archive.getnames()) == EXPECTED_MEMBERS
        for member in archive.getmembers():
            assert (member.mode, member.mtime, member.uid, member.gid) == (
                0o644,
                0,
                0,
                0,
            )
            assert (member.uname, member.gname) == ("", "")
            assert member.isfile()
        extracted = archive.extractfile("ARTIFACT_MANIFEST.txt")
        assert extracted is not None
        manifest = extracted.read().decode("utf-8")

    assert "commit: " + "a" * 40 in manifest
    assert "dirtyWorktree: false" in manifest
    assert "geometryIncluded: false" in manifest
    assert f"geometryCommit: {transfer.FRONTEND_GEOMETRY_COMMIT}" in manifest
    assert "geometryRequiredFiles: assur.geojson, kalhu.geojson" in manifest
    assert "mappingCount: 315" in manifest
    assert "mappingCount: 129" in manifest
    assert "mappingCount: 7" in manifest
    assert "mappingCount: 18" in manifest


def test_manifest_marks_dirty_git_provenance(tmp_path, monkeypatch):
    def dirty_git(*args: str) -> str:
        if args[0] == "status":
            return " M ebl/fragmentarium/data/map/assur_polygon_inventory.json"
        if "--abbrev-ref" in args:
            return "review-757"
        return "b" * 40

    monkeypatch.setattr(transfer, "_git", dirty_git)
    output = transfer.build_archive(DEFAULT_OUTPUT_DIR, tmp_path / "transfer.tar.gz")

    with tarfile.open(output, "r:gz") as archive:
        extracted = archive.extractfile("ARTIFACT_MANIFEST.txt")
        assert extracted is not None
        assert "dirtyWorktree: true" in extracted.read().decode("utf-8")


def test_checksum_tampering_is_rejected_before_output(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    target = data_dir / "assur_findspot_polygon_mappings.json"
    target.write_bytes(target.read_bytes() + b"\n")
    output = tmp_path / "transfer.tar.gz"

    with pytest.raises(ValueError, match="checksum mismatch"):
        transfer.build_archive(data_dir, output)

    assert not output.exists()


def test_mixed_site_content_is_rejected_even_with_updated_checksum(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    wrong_content = (data_dir / "nippur_findspot_polygon_mappings.json").read_bytes()
    _replace_declared_file(
        data_dir, "assur_findspot_polygon_mappings.json", wrong_content
    )

    with pytest.raises(ValueError, match="Invalid mapping identity"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


def test_ambiguous_json_is_rejected_even_with_updated_checksum(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    _replace_declared_file(
        data_dir,
        "assur_polygon_inventory.json",
        b'[{"polygonId":"one","polygonId":"two"}]',
    )

    with pytest.raises(ValueError, match="Duplicate JSON key"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


def test_symlinked_source_artifact_is_rejected(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    target = data_dir / "assur_polygon_inventory.json"
    original = tmp_path / "original.json"
    target.replace(original)
    target.symlink_to(original)

    with pytest.raises(FileNotFoundError, match="Missing regular artifact"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


def test_write_failure_preserves_source_and_previous_output(tmp_path, monkeypatch):
    data_dir = _copy_artifacts(tmp_path)
    sentinel = data_dir / "ARTIFACT_MANIFEST.txt"
    sentinel.write_text("keep me", encoding="utf-8")
    before = _directory_snapshot(data_dir)
    output = tmp_path / "transfer.tar.gz"
    output.write_bytes(b"previous archive")

    def fail_write(path: Path, members: tuple[tuple[str, bytes], ...]) -> None:
        path.write_bytes(b"partial")
        raise OSError("injected archive failure")

    monkeypatch.setattr(transfer, "_write_archive", fail_write)
    with pytest.raises(OSError, match="injected archive failure"):
        transfer.build_archive(data_dir, output)

    assert output.read_bytes() == b"previous archive"
    assert _directory_snapshot(data_dir) == before
    assert not list(tmp_path.glob(".transfer.tar.gz.*.tmp"))


def test_output_inside_source_or_through_symlink_is_rejected(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    with pytest.raises(ValueError, match="outside the source"):
        transfer.build_archive(data_dir, data_dir / "transfer.tar.gz")

    output = tmp_path / "transfer.tar.gz"
    output.symlink_to(tmp_path / "target.tar.gz")
    with pytest.raises(ValueError, match="symbolic link"):
        transfer.build_archive(data_dir, output)


def test_archive_member_names_must_be_basenames():
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        with pytest.raises(ValueError, match="must be a basename"):
            transfer._add_member(archive, "../escape", b"payload")


def test_invalid_inventory_contract_is_rejected(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    name = "assur_polygon_inventory.json"
    inventory = json.loads((data_dir / name).read_text(encoding="utf-8"))
    inventory[0].pop("geometryChecksum")
    _replace_declared_file(data_dir, name, json.dumps(inventory).encode("utf-8"))

    with pytest.raises(ValueError, match="Invalid inventory record"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


@pytest.mark.parametrize(
    ("field", "value"),
    (("locationPrecision", "invalid"), ("matchMethod", "invented"), ("source", "")),
)
def test_invalid_mapping_contract_is_rejected(tmp_path, field, value):
    data_dir = _copy_artifacts(tmp_path)
    name = "assur_findspot_polygon_mappings.json"
    mappings = json.loads((data_dir / name).read_text(encoding="utf-8"))
    mappings[0][field] = value
    _replace_declared_file(data_dir, name, json.dumps(mappings).encode("utf-8"))

    with pytest.raises(ValidationError):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


@pytest.mark.parametrize("findspot_id", (-1, MAX_FINDSPOT_ID + 1))
def test_mapping_findspot_id_must_fit_nonnegative_bson_int64(tmp_path, findspot_id):
    data_dir = _copy_artifacts(tmp_path)
    name = "assur_findspot_polygon_mappings.json"
    mappings = json.loads((data_dir / name).read_text(encoding="utf-8"))
    mappings[0]["findspotId"] = findspot_id
    _replace_declared_file(data_dir, name, json.dumps(mappings).encode("utf-8"))

    with pytest.raises(ValueError, match="Invalid mapping identity"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


def test_mapping_allows_zero_and_independent_curated_revision(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    name = "assur_findspot_polygon_mappings.json"
    mappings = json.loads((data_dir / name).read_text(encoding="utf-8"))
    mappings[0].update(
        findspotId=0,
        matchMethod="curated",
        source="reviewed register",
        sourceRevision="register-2026-09-25",
    )
    _replace_declared_file(data_dir, name, json.dumps(mappings).encode("utf-8"))

    assert transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz").is_file()
