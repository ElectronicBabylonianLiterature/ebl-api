import json
from pathlib import Path

import pytest

from scripts.maps.map_artifact_generator import (
    build_site_artifacts,
    write_site_artifacts,
)
from scripts.maps.map_site_config import SITE_CONFIGS


@pytest.fixture(scope="module")
def reviewed_curation() -> str:
    artifacts = build_site_artifacts(SITE_CONFIGS["KALHU"], "reviewed")
    row = artifacts["curation"][0].copy()
    row["polygonIds"] = [artifacts["inventory"][0]["polygonId"]]
    row["reviewer"] = "reviewer-handle"
    row["reviewDate"] = "2026-11-06"
    return json.dumps([row])


@pytest.mark.parametrize(
    "suffix",
    [
        "polygon_inventory",
        "findspot_polygon_mappings",
        "findspot_polygon_curation_report",
        "artifact_manifest",
    ],
)
def test_curation_input_cannot_alias_other_publication_targets(
    tmp_path: Path, reviewed_curation: str, suffix: str
) -> None:
    path = tmp_path / f"kalhu_{suffix}.json"
    path.write_text(reviewed_curation, encoding="utf-8")

    with pytest.raises(ValueError, match="must not alias"):
        write_site_artifacts(SITE_CONFIGS["KALHU"], tmp_path, "reviewed", path)

    assert path.read_text(encoding="utf-8") == reviewed_curation
    assert list(tmp_path.iterdir()) == [path]


def test_external_reviewed_input_survives_repeat_publication(
    tmp_path: Path, reviewed_curation: str
) -> None:
    path = tmp_path / "reviewed.json"
    path.write_text(reviewed_curation, encoding="utf-8")
    output = tmp_path / "output"

    first = write_site_artifacts(SITE_CONFIGS["KALHU"], output, "reviewed", path)
    repeated = write_site_artifacts(SITE_CONFIGS["KALHU"], output, "reviewed", path)

    assert first["mappings"] == repeated["mappings"]
    assert any(row["matchMethod"] == "curated" for row in repeated["mappings"])
    assert path.read_text(encoding="utf-8") == reviewed_curation
