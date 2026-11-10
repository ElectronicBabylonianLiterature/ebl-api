from dataclasses import replace

import pytest

from scripts.maps.map_site_config import SITE_CONFIGS


def test_site_config_rejects_unknown_ods_columns() -> None:
    with pytest.raises(ValueError, match="Unknown ODS columns.*unknown"):
        replace(SITE_CONFIGS["ASSUR"], ods_header=("_id", "unknown"))


def test_site_config_rejects_unknown_match_fields() -> None:
    with pytest.raises(ValueError, match="Unknown match fields.*room"):
        replace(SITE_CONFIGS["ASSUR"], match_fields=("room",))


@pytest.mark.parametrize(
    "site_id, expected_crs, requires_reprojection",
    [("ASSUR", "EPSG:4326", False), ("KALHU", "EPSG:3857", True)],
)
def test_site_config_derives_reprojection_from_explicit_source_crs(
    site_id: str, expected_crs: str, requires_reprojection: bool
) -> None:
    config = SITE_CONFIGS[site_id]

    assert config.source_crs == expected_crs
    assert config.requires_reprojection is requires_reprojection
