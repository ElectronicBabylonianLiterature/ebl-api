import hashlib
from pathlib import Path

from ebl.fragmentarium.application.assur_map_artifacts import (
    build_assur_artifacts,
    write_assur_artifacts,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_build_assur_artifacts_counts_and_links():
    artifacts = build_assur_artifacts("2026-07-27")
    inventory_ids = {item["polygonId"] for item in artifacts["inventory"]}

    assert len(artifacts["inventory"]) == 134
    assert len(artifacts["mappings"]) == 304
    assert len(artifacts["curation"]) == 42
    assert all(item["polygonIds"][0] in inventory_ids for item in artifacts["mappings"])
    assert all(
        record.status in {"verified-mapped", "needs-human-curation"}
        for record in artifacts["derivations"]
    )


def test_write_assur_artifacts_is_reproducible(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"

    write_assur_artifacts(left, "2026-07-27")
    write_assur_artifacts(right, "2026-07-27")

    assert {path.name: _digest(path) for path in sorted(left.iterdir())} == {
        path.name: _digest(path) for path in sorted(right.iterdir())
    }
