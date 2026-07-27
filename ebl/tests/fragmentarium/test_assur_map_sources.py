import pytest

from ebl.fragmentarium.application.assur_map_sources import (
    build_assur_polygon_id,
    load_assur_ods_rows,
    load_assur_polygons,
    normalize_assur_area_label,
    shapefile_area_name,
)


def test_load_assur_sources_counts():
    assert len(load_assur_ods_rows()) == 346
    polygons = load_assur_polygons()
    assert len(polygons) == 134
    assert len({polygon.name for polygon in polygons}) == 134
    assert len({polygon.polygon_id for polygon in polygons}) == 134


def test_normalize_assur_area_label_matches_source_rule():
    assert normalize_assur_area_label("i3? town area") == "i3 town area"
    assert shapefile_area_name("26dD9IV") == "dD9IV"


def test_polygon_id_is_stable_across_rotation_and_orientation():
    ring = (
        (43.0, 35.0),
        (43.1, 35.0),
        (43.1, 35.1),
        (43.0, 35.1),
        (43.0, 35.0),
    )
    rotated = ring[1:-1] + ring[:2]
    reversed_ring = tuple(reversed(ring))
    polygon_id, checksum = build_assur_polygon_id("2bC5II", (ring,))

    assert build_assur_polygon_id("2bC5II", (rotated,)) == (polygon_id, checksum)
    assert build_assur_polygon_id("2bC5II", (reversed_ring,)) == (polygon_id, checksum)


def test_polygon_id_rejects_invalid_geometry():
    with pytest.raises(ValueError, match="closed"):
        build_assur_polygon_id("broken", (((43.0, 35.0), (43.1, 35.0), (43.1, 35.1)),))
