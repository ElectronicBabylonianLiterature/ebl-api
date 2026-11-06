import json
import pytest
from pathlib import Path

from ebl.fragmentarium.application.map_artifact_generator import build_site_artifacts
from ebl.fragmentarium.application.map_curated_mappings import load_curated_mappings
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.application.map_source_loader import load_site_ods_rows


def test_generated_curation_template_can_be_completed_and_loaded(
    tmp_path: Path,
) -> None:
    config = SITE_CONFIGS["KALHU"]
    artifacts = build_site_artifacts(config, " revision-1 ")
    row = dict(artifacts["curation"][0])
    row.update(
        polygonIds=[artifacts["inventory"][0]["polygonId"]],
        reviewer="reviewer-handle",
        reviewDate="2026-09-25",
    )
    path = tmp_path / "curated.json"
    template = [dict(item) for item in artifacts["curation"]]
    template[0] = row
    path.write_text(json.dumps(template), encoding="utf-8")

    records = load_curated_mappings(
        path,
        config.site_id,
        {item["polygonId"] for item in artifacts["inventory"]},
        {source_row.findspot_id for source_row in load_site_ods_rows(config)},
    )

    assert records[0]["sourceRevision"] == "revision-1"
    regenerated = build_site_artifacts(config, "revision-1", path)
    assert len(regenerated["curation"]) == len(artifacts["curation"]) - 1
    assert (
        regenerated["curation"][0]["sourceRows"]
        == artifacts["curation"][1]["sourceRows"]
    )


def test_unreviewed_ambiguous_uruk_template_roundtrips_without_assignments(
    tmp_path: Path,
) -> None:
    config = SITE_CONFIGS["URUK"]
    original = build_site_artifacts(config, "revision-1")
    path = tmp_path / "pending.json"
    path.write_text(json.dumps(original["curation"]), encoding="utf-8")

    rebuilt = build_site_artifacts(config, "revision-1", path)

    assert rebuilt == original
    ambiguous = next(row for row in rebuilt["curation"] if row["findspotId"] == 1)
    assert ambiguous["derivationStatus"] == "unresolved"
    assert ambiguous["membershipStatus"] == "unverified-or-conflicting"
    assert ambiguous["candidatePolygonIds"] == []
    assert len(ambiguous["sourceRows"]) > 1


def test_curation_rejects_source_context_for_another_findspot(tmp_path: Path) -> None:
    config = SITE_CONFIGS["KALHU"]
    artifacts = build_site_artifacts(config, "revision-1")
    original = artifacts["curation"][0]
    row = {
        **original,
        "sourceRows": [{**original["sourceRows"][0], "findspotId": 99999}],
    }
    path = tmp_path / "mixed-context.json"
    path.write_text(json.dumps([row]), encoding="utf-8")

    with pytest.raises(ValueError, match="sourceRows"):
        build_site_artifacts(config, "revision-1", path)
