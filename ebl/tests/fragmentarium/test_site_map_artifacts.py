import hashlib
from pathlib import Path

from ebl.fragmentarium.application.map_artifact_generator import (
    build_site_artifacts,
    write_site_artifacts,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_uruk_artifacts_bypass_corrupted_id_and_disambiguate_duplicate_name():
    artifacts = build_site_artifacts(SITE_CONFIGS["URUK"], "2026-08-05")
    inventory = artifacts["inventory"]

    assert len(inventory) == 128
    duplicate_name_entries = [item for item in inventory if item["name"] == "Pd XVI/4"]
    assert len(duplicate_name_entries) == 2
    assert (
        duplicate_name_entries[0]["polygonId"] != duplicate_name_entries[1]["polygonId"]
    )

    mapped_polygon_ids = {
        polygon_id
        for mapping in artifacts["mappings"]
        for polygon_id in mapping["polygonIds"]
    }
    duplicate_ids = {item["polygonId"] for item in duplicate_name_entries}
    assert not (mapped_polygon_ids & duplicate_ids)

    findspot_ids = {mapping["findspotId"] for mapping in artifacts["mappings"]}
    assert len(findspot_ids) == len(artifacts["mappings"])


def test_nippur_artifacts_flag_conflicting_duplicate_rows_as_curation():
    artifacts = build_site_artifacts(SITE_CONFIGS["NIPPUR"], "2026-08-05")

    assert len(artifacts["inventory"]) == 20
    conflict_rows = [
        item
        for item in artifacts["curation"]
        if "conflict" in item["requiredDecision"].lower()
    ]
    assert len(conflict_rows) == 1
    assert conflict_rows[0]["findspotId"] == 4263


def test_kalhu_artifacts_reproject_and_report_low_coverage():
    artifacts = build_site_artifacts(SITE_CONFIGS["KALHU"], "2026-08-05")

    assert len(artifacts["inventory"]) == 12
    covered = len(artifacts["mappings"]) + len(artifacts["curation"])
    assert covered == 18
    assert len(artifacts["mappings"]) < len(artifacts["curation"])


def test_no_site_produces_duplicate_findspot_mappings():
    for site_id in SITE_CONFIGS:
        artifacts = build_site_artifacts(SITE_CONFIGS[site_id], "2026-08-05")
        ids = [mapping["findspotId"] for mapping in artifacts["mappings"]]
        assert len(ids) == len(set(ids))


def test_site_artifact_generation_is_deterministic(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"

    for config in SITE_CONFIGS.values():
        write_site_artifacts(config, left, "2026-08-05")
        write_site_artifacts(config, right, "2026-08-05")

    assert {path.name: _digest(path) for path in sorted(left.iterdir())} == {
        path.name: _digest(path) for path in sorted(right.iterdir())
    }
