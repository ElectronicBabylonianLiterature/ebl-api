import hashlib
from pathlib import Path

from scripts.maps.map_artifact_generator import (
    build_site_artifacts,
    write_site_artifacts,
)
from scripts.maps.map_site_config import SITE_CONFIGS


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_build_assur_artifacts_counts_and_links() -> None:
    artifacts = build_site_artifacts(SITE_CONFIGS["ASSUR"], "2026-07-27")
    inventory_ids = {item["polygonId"] for item in artifacts["inventory"]}

    assert len(artifacts["inventory"]) == 134
    assert len(artifacts["mappings"]) == 315
    assert len(artifacts["curation"]) == 31
    assert len({item["polygonIds"][0] for item in artifacts["mappings"]}) == 133
    assert all(item["polygonIds"][0] in inventory_ids for item in artifacts["mappings"])
    assert all(
        record.status in {"verified-mapped", "needs-human-curation"}
        for record in artifacts["derivations"]
    )
    assert {4392, 4658} <= {record["findspotId"] for record in artifacts["curation"]}


def test_write_assur_artifacts_is_reproducible(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"

    write_site_artifacts(SITE_CONFIGS["ASSUR"], left, "2026-07-27")
    write_site_artifacts(SITE_CONFIGS["ASSUR"], right, "2026-07-27")

    assert {path.name: _digest(path) for path in sorted(left.iterdir())} == {
        path.name: _digest(path) for path in sorted(right.iterdir())
    }
