import unicodedata

import pytest

from scripts.maps.map_polygon_identity import (
    build_polygon_id,
    normalize_label,
    polygon_match_key as shapefile_area_name,
)
from scripts.maps.map_site_config import SITE_CONFIGS
from scripts.maps.map_source_loader import load_site_ods_rows, load_site_polygons


def test_load_assur_sources_counts() -> None:
    assert len(load_site_ods_rows(SITE_CONFIGS["ASSUR"])) == 346
    polygons = load_site_polygons(SITE_CONFIGS["ASSUR"])
    assert len(polygons) == 134
    assert len({polygon.name for polygon in polygons}) == 134
    assert len({polygon.polygon_id for polygon in polygons}) == 134
    assert polygons[0].name == "bB6I"
    assert all(
        unicodedata.category(character) != "Cc"
        for polygon in polygons
        for character in polygon.name
    )


def test_normalize_assur_area_label_matches_source_rule() -> None:
    assert normalize_label("i3? town area") == "i3? town area"
    assert shapefile_area_name("26dD9IV") == "dD9IV"


def test_polygon_id_is_stable_across_rotation_and_orientation() -> None:
    ring = (
        (43.0, 35.0),
        (43.1, 35.0),
        (43.1, 35.1),
        (43.0, 35.1),
        (43.0, 35.0),
    )
    rotated = ring[1:-1] + ring[:2]
    reversed_ring = tuple(reversed(ring))
    polygon_id, checksum = build_polygon_id("assur", "2bC5II", ((ring,),))

    assert build_polygon_id("assur", "2bC5II", ((rotated,),)) == (polygon_id, checksum)
    assert build_polygon_id("assur", "2bC5II", ((reversed_ring,),)) == (
        polygon_id,
        checksum,
    )


def test_polygon_id_rejects_invalid_geometry() -> None:
    with pytest.raises(ValueError, match="closed"):
        build_polygon_id(
            "assur", "broken", ((((43.0, 35.0), (43.1, 35.0), (43.1, 35.1)),),)
        )
