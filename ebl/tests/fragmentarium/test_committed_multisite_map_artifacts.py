import pytest

from ebl.fragmentarium.application.map_artifact_generator import (
    write_site_artifacts,
)
from ebl.fragmentarium.application.map_paths import MAP_DATA_DIR
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS


@pytest.mark.parametrize("site_id", ["URUK", "KALHU", "NIPPUR"])
def test_committed_multisite_artifacts_match_generator_output(tmp_path, site_id):
    write_site_artifacts(SITE_CONFIGS[site_id], tmp_path, "2026-08-05")
    prefix = site_id.lower()
    generated = sorted(tmp_path.glob(f"{prefix}_*"))

    assert len(generated) == 5
    assert all(
        path.read_bytes() == (MAP_DATA_DIR / path.name).read_bytes()
        for path in generated
    )
