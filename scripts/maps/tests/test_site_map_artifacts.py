import hashlib
import json
from pathlib import Path

import pytest

from scripts.maps.map_artifact_generator import (
    build_site_artifacts,
    write_site_artifacts,
)
from scripts.maps.map_site_config import SITE_CONFIGS
from scripts.maps.map_membership import MembershipEvidence
from scripts.maps.map_source_loader import (
    MapOdsRow,
    MapPolygon,
    SiteSources,
    load_site_ods_rows,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_uruk_artifacts_bypass_corrupted_id_and_disambiguate_duplicate_name() -> None:
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


def test_nippur_artifacts_flag_conflicting_duplicate_rows_as_curation() -> None:
    artifacts = build_site_artifacts(SITE_CONFIGS["NIPPUR"], "2026-08-05")

    assert len(artifacts["inventory"]) == 20
    conflict_rows = [
        item
        for item in artifacts["curation"]
        if "conflict" in item["requiredDecision"].lower()
    ]
    assert {row["findspotId"] for row in conflict_rows} == {901, 2538, 4263}
    assert all(row["derivationStatus"] == "conflict" for row in conflict_rows)
    assert all(row["candidatePolygonIds"] for row in conflict_rows)


def test_kalhu_artifacts_reproject_and_report_low_coverage() -> None:
    artifacts = build_site_artifacts(SITE_CONFIGS["KALHU"], "2026-08-05")

    assert len(artifacts["inventory"]) == 12
    covered = len(artifacts["mappings"]) + len(artifacts["curation"])
    assert covered == 18
    assert len(artifacts["mappings"]) < len(artifacts["curation"])
    labels = json.loads(artifacts["report"])["unresolvedLabels"]
    assert {"label": "Governor's Palace", "count": 1} in labels
    assert {"label": "<blank>", "count": 7} not in labels


def test_no_site_produces_duplicate_findspot_mappings() -> None:
    for site_id in SITE_CONFIGS:
        artifacts = build_site_artifacts(SITE_CONFIGS[site_id], "2026-08-05")
        ids = [mapping["findspotId"] for mapping in artifacts["mappings"]]
        assert len(ids) == len(set(ids))


def test_mixed_evidence_findspots_are_not_published_as_verified_mappings() -> None:
    affected = {"URUK": {1, 44}, "KALHU": {228}, "NIPPUR": {901, 2538}}

    for site_id, findspot_ids in affected.items():
        artifacts = build_site_artifacts(SITE_CONFIGS[site_id], "2026-08-05")
        mapped_ids = {mapping["findspotId"] for mapping in artifacts["mappings"]}
        curation_ids = {row["findspotId"] for row in artifacts["curation"]}
        assert not mapped_ids & findspot_ids
        assert findspot_ids <= curation_ids


def test_kalhu_curation_template_preserves_building_decision_evidence() -> None:
    artifacts = build_site_artifacts(SITE_CONFIGS["KALHU"], "revision-1")

    row = next(item for item in artifacts["curation"] if item["findspotId"] == 348)

    assert row["area"] == ""
    assert row["building"] == "Governor's Palace"


def test_blank_source_revision_is_rejected() -> None:
    with pytest.raises(ValueError, match="sourceRevision"):
        build_site_artifacts(SITE_CONFIGS["ASSUR"], "  ")


def test_additional_authoritative_membership_supports_non_ods_curation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "curated.json"
    path.write_text(
        json.dumps(
            [
                {
                    "findspotId": 1,
                    "siteId": "ASSUR",
                    "polygonIds": ["assur-area-checksum"],
                    "matchMethod": "curated",
                    "reviewer": "reviewer-handle",
                    "reviewDate": "2026-09-25",
                    "source": "authoritative site register",
                    "sourceRevision": "register-1",
                },
                {
                    "findspotId": 2,
                    "siteId": "ASSUR",
                    "polygonIds": ["assur-area-checksum"],
                    "matchMethod": "curated",
                    "reviewer": "reviewer-handle",
                    "reviewDate": "2026-09-25",
                    "source": "authoritative site register",
                    "sourceRevision": "register-1",
                },
            ]
        ),
        encoding="utf-8",
    )

    artifacts = build_site_artifacts(
        SITE_CONFIGS["ASSUR"],
        "revision-1",
        curated_records_path=path,
        sources=SiteSources(
            membership_evidence=MembershipEvidence(
                "independent fixture register",
                "register-1",
                {1: frozenset(("Aššur",)), 2: frozenset(("Aššur",))},
            ),
            ods_rows=(MapOdsRow(findspot_id=1, area="unknown"),),
            polygons=(
                MapPolygon(
                    name="Area",
                    polygon_id="assur-area-checksum",
                    geometry_checksum="checksum",
                ),
            ),
        ),
        additional_authoritative_findspot_ids={1, 2},
    )

    assert [record["findspotId"] for record in artifacts["mappings"]] == [1, 2]
    counts = json.loads(artifacts["report"])["counts"]
    assert counts["curatedMappings"] == 2
    assert counts["curatedMappingsWithoutSourceGroups"] == 1


@pytest.mark.parametrize("site_name", ["", "Wrong site"])
def test_ods_rows_without_canonical_site_cannot_authorize_curation(
    tmp_path: Path, site_name: str
) -> None:
    path = tmp_path / "curated.json"
    path.write_text(
        json.dumps(
            [
                {
                    "findspotId": 1,
                    "siteId": "ASSUR",
                    "polygonIds": ["assur-area-checksum"],
                    "matchMethod": "curated",
                    "reviewer": "reviewer-handle",
                    "reviewDate": "2026-09-25",
                    "source": "human curation",
                    "sourceRevision": "revision-1",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="authoritative membership"):
        build_site_artifacts(
            SITE_CONFIGS["ASSUR"],
            "revision-1",
            curated_records_path=path,
            sources=SiteSources(
                ods_rows=(MapOdsRow(findspot_id=1, site_name=site_name, area="Area"),),
                polygons=(
                    MapPolygon(
                        name="Area",
                        polygon_id="assur-area-checksum",
                        geometry_checksum="checksum",
                    ),
                ),
            ),
        )


def test_uruk_blank_site_rows_do_not_supply_membership_evidence() -> None:
    rows = load_site_ods_rows(SITE_CONFIGS["URUK"])

    assert {row.findspot_id for row in rows if not row.site_name} == {1, 2}


@pytest.mark.parametrize("findspot_id", [True, -1, 2**63])
def test_invalid_additional_membership_evidence_is_rejected(
    findspot_id: int,
) -> None:
    with pytest.raises(ValueError, match="BSON int64"):
        build_site_artifacts(
            SITE_CONFIGS["ASSUR"],
            "revision-1",
            sources=SiteSources(ods_rows=(), polygons=()),
            additional_authoritative_findspot_ids={findspot_id},
        )


def test_site_artifact_generation_is_deterministic(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"

    for config in SITE_CONFIGS.values():
        write_site_artifacts(config, left, "2026-08-05")
        write_site_artifacts(config, right, "2026-08-05")

    assert {path.name: _digest(path) for path in sorted(left.iterdir())} == {
        path.name: _digest(path) for path in sorted(right.iterdir())
    }
