import pytest
import json
from pathlib import Path

from ebl.fragmentarium.application.map_artifact_generator import (
    write_site_artifacts,
)
from ebl.fragmentarium.application.map_paths import MAP_DATA_DIR
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.application.map_membership import load_membership_evidence
from ebl.fragmentarium.application.map_artifact_storage import read_validated_artifact


@pytest.mark.parametrize("site_id", ["ASSUR", "URUK", "KALHU", "NIPPUR"])
def test_committed_multisite_artifacts_match_generator_output(
    tmp_path: Path, site_id: str
) -> None:
    revision = "2026-07-27" if site_id == "ASSUR" else "2026-08-05"
    write_site_artifacts(SITE_CONFIGS[site_id], tmp_path, revision)
    prefix = site_id.lower()
    generated = sorted(tmp_path.glob(f"{prefix}_*"))

    assert len(generated) == 5
    mismatched = [
        path.name
        for path in generated
        if path.read_bytes() != (MAP_DATA_DIR / path.name).read_bytes()
    ]
    assert mismatched == []


def test_committed_four_site_identity_membership_and_uncertainty_are_consistent() -> (
    None
):
    expected = {
        "ASSUR": (134, 315, 31),
        "KALHU": (12, 7, 11),
        "NIPPUR": (20, 18, 10),
        "URUK": (128, 129, 14),
    }
    evidence = load_membership_evidence()
    all_polygon_ids: set[str] = set()
    all_findspot_ids: set[int] = set()
    unverified: set[int] = set()
    for site_id, counts in expected.items():
        prefix = site_id.lower()
        inventory = json.loads(
            read_validated_artifact(
                MAP_DATA_DIR, prefix, f"{prefix}_polygon_inventory.json"
            )
        )
        mappings = json.loads(
            read_validated_artifact(
                MAP_DATA_DIR, prefix, f"{prefix}_findspot_polygon_mappings.json"
            )
        )
        pending = json.loads(
            read_validated_artifact(
                MAP_DATA_DIR,
                prefix,
                f"{prefix}_findspot_polygon_curation_template.json",
            )
        )
        report = json.loads(
            read_validated_artifact(
                MAP_DATA_DIR, prefix, f"{prefix}_findspot_polygon_curation_report.json"
            )
        )
        assert (len(inventory), len(mappings), len(pending)) == counts
        polygon_ids = {row["polygonId"] for row in inventory}
        findspot_ids = {row["findspotId"] for row in mappings}
        assert len(polygon_ids) == len(inventory)
        assert len(findspot_ids) == len(mappings)
        assert not all_polygon_ids & polygon_ids
        assert not all_findspot_ids & findspot_ids
        assert findspot_ids <= evidence.findspot_ids_for(
            SITE_CONFIGS[site_id].site_name
        )
        assert {row["siteId"] for row in inventory} == {site_id}
        assert all(set(row["polygonIds"]) <= polygon_ids for row in mappings)
        assert all(row["polygonIds"] == [] and row["sourceRows"] for row in pending)
        assert all(set(row["candidatePolygonIds"]) <= polygon_ids for row in pending)
        assert report["schemaVersion"] == 1
        assert report["membershipSourceRevision"] == evidence.source_revision
        unverified.update(
            row["findspotId"]
            for row in pending
            if row["membershipStatus"] != "confirmed"
        )
        all_polygon_ids.update(polygon_ids)
        all_findspot_ids.update(findspot_ids)
    assert len(all_polygon_ids) == 294
    assert len(all_findspot_ids) == 469
    assert unverified == {1, 2}
