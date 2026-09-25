import hashlib
import json
from pathlib import Path
import shutil

import pytest

from ebl.fragmentarium.application.map_artifact_generator import DEFAULT_OUTPUT_DIR
from scripts.maps import frontend_transfer_archive as transfer
from scripts.maps.frontend_transfer_validation import read_artifact_sets


def _copy_artifacts(tmp_path: Path) -> Path:
    destination = tmp_path / "artifacts"
    shutil.copytree(DEFAULT_OUTPUT_DIR, destination)
    return destination


def _replace_declared_file(data_dir: Path, name: str, payload: object) -> None:
    content = json.dumps(payload).encode("utf-8")
    (data_dir / name).write_bytes(content)
    manifest_path = data_dir / f"{name.split('_', 1)[0]}_artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name] = hashlib.sha256(content).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def test_inventory_area_name_must_be_nonblank(tmp_path):
    data_dir = _copy_artifacts(tmp_path)
    name = "assur_polygon_inventory.json"
    inventory = json.loads((data_dir / name).read_text(encoding="utf-8"))
    inventory[0]["areaName"] = ""
    _replace_declared_file(data_dir, name, inventory)

    with pytest.raises(ValueError, match="Invalid inventory identity"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


@pytest.mark.parametrize(
    ("name", "mutation", "message"),
    (
        (
            "assur_polygon_inventory.json",
            {"unrelatedPrivateField": "synthetic-sentinel"},
            "Invalid inventory record",
        ),
        (
            "assur_findspot_polygon_mappings.json",
            {"unrelatedPrivateField": "synthetic-sentinel"},
            "Invalid mapping record",
        ),
    ),
)
def test_unknown_transferred_fields_are_rejected(tmp_path, name, mutation, message):
    data_dir = _copy_artifacts(tmp_path)
    records = json.loads((data_dir / name).read_text(encoding="utf-8"))
    records[0].update(mutation)
    _replace_declared_file(data_dir, name, records)
    output = tmp_path / "transfer.tar.gz"

    with pytest.raises(ValueError, match=message):
        transfer.build_archive(data_dir, output)

    assert not output.exists()


@pytest.mark.parametrize(
    "mutation", ({"reviewer": "reviewed"}, {"area": 17}, {"reviewDate": None})
)
def test_curation_template_contract_is_exact(tmp_path, mutation):
    data_dir = _copy_artifacts(tmp_path)
    name = "assur_findspot_polygon_curation_template.json"
    records = json.loads((data_dir / name).read_text(encoding="utf-8"))
    records[0].update(mutation)
    _replace_declared_file(data_dir, name, records)

    with pytest.raises(ValueError, match="Invalid curation template"):
        transfer.build_archive(data_dir, tmp_path / "transfer.tar.gz")


def test_manifest_embeds_exact_frontend_reproduction_inputs(monkeypatch):
    monkeypatch.setattr(
        transfer, "_git", lambda *args: "" if args[0] == "status" else "a" * 40
    )
    contents, revisions = read_artifact_sets(DEFAULT_OUTPUT_DIR)
    manifest = transfer.build_manifest(contents, revisions).decode("utf-8")
    expectations = json.dumps(
        transfer.FRONTEND_GENERATOR_EXPECTATIONS, separators=(",", ":")
    )

    assert f"frontendGeneratorPath: {transfer.FRONTEND_GENERATOR_PATH}" in manifest
    assert f"frontendGeneratorExpectationsJson: {expectations}" in manifest
