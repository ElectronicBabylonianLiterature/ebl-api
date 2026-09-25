from dataclasses import replace

import pytest

import ebl.fragmentarium.application.map_source_loader as source_loader

from ebl.fragmentarium.application.map_findspot_grouping import group_findspots
from ebl.fragmentarium.application.map_mapping_rules import (
    derive_row,
    index_polygons_by_key,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.application.map_source_loader import (
    MapOdsRow,
    MapPolygon,
    load_site_ods_rows,
    load_site_polygons,
)


def test_load_site_ods_rows_rejects_unexpected_header():
    config = replace(SITE_CONFIGS["ASSUR"], ods_header=("site", "_id", "area"))

    with pytest.raises(ValueError, match="Unexpected ODS header"):
        load_site_ods_rows(config)


def test_load_site_ods_rows_skips_blank_id_rows():
    rows = load_site_ods_rows(SITE_CONFIGS["ASSUR"])

    assert all(row.findspot_id for row in rows)


def test_source_paths_and_loading_do_not_depend_on_working_directory(
    tmp_path, monkeypatch
):
    config = SITE_CONFIGS["ASSUR"]
    assert config.ods_path.is_absolute()
    assert config.shp_base.is_absolute()

    monkeypatch.chdir(tmp_path)

    assert load_site_ods_rows(config)


@pytest.mark.parametrize("raw_id", ["-1", "1.0", "١", str(2**63)])
def test_load_site_ods_rows_rejects_invalid_findspot_ids(monkeypatch, raw_id):
    config = SITE_CONFIGS["ASSUR"]
    monkeypatch.setattr(
        source_loader,
        "read_ods_rows",
        lambda path: (config.ods_header, (raw_id, "area", "sector", "site", "map")),
    )

    with pytest.raises(ValueError, match="Invalid findspot ID"):
        load_site_ods_rows(config)


def test_group_findspots_deduplicates_agreeing_progressive_rows():
    config = SITE_CONFIGS["KALHU"]
    rows = (
        MapOdsRow(findspot_id=1, area="D XII"),
        MapOdsRow(findspot_id=1, area="D XII"),
    )
    polygons = (
        MapPolygon(name="D XII", polygon_id="kalhu-d-xii-abc", geometry_checksum="abc"),
    )
    index = index_polygons_by_key(polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)

    groups = group_findspots(rows, derivations)

    assert len(groups) == 1
    assert groups[0].status == "resolved"
    assert groups[0].polygon_id == "kalhu-d-xii-abc"


def test_group_findspots_flags_disagreeing_rows_as_conflict():
    config = SITE_CONFIGS["KALHU"]
    rows = (
        MapOdsRow(findspot_id=1, area="D XII"),
        MapOdsRow(findspot_id=1, area="ZT"),
    )
    polygons = (
        MapPolygon(name="D XII", polygon_id="kalhu-d-xii-abc", geometry_checksum="abc"),
        MapPolygon(name="ZT", polygon_id="kalhu-zt-def", geometry_checksum="def"),
    )
    index = index_polygons_by_key(polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)

    groups = group_findspots(rows, derivations)

    assert len(groups) == 1
    assert groups[0].status == "conflict"
    assert groups[0].polygon_id is None


def test_load_site_polygons_rejects_semantically_different_crs(monkeypatch):
    from pyproj import CRS

    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_dbf_encoding",
        lambda path: "UTF-8",
    )
    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_dbf_rows",
        lambda path, encoding: ({"Name": "A"},),
    )
    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_shp_polygon_geometries",
        lambda path: (((((43.0, 35.0), (43.0, 35.1), (43.1, 35.1), (43.0, 35.0)),),),),
    )
    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_prj_wkt",
        lambda path: CRS.from_epsg(3857).to_wkt(),
    )

    with pytest.raises(ValueError, match="does not match"):
        load_site_polygons(SITE_CONFIGS["ASSUR"])


def test_load_site_polygons_always_checks_geographic_bounds(monkeypatch):
    from pyproj import CRS

    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_dbf_encoding",
        lambda path: "UTF-8",
    )
    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_dbf_rows",
        lambda path, encoding: ({"Name": "A"},),
    )
    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_shp_polygon_geometries",
        lambda path: (
            ((((200.0, 35.0), (200.0, 35.1), (200.1, 35.1), (200.0, 35.0)),),),
        ),
    )
    monkeypatch.setattr(
        "ebl.fragmentarium.application.map_source_loader.load_prj_wkt",
        lambda path: CRS.from_epsg(4326).to_wkt(),
    )

    with pytest.raises(ValueError, match="plausible"):
        load_site_polygons(SITE_CONFIGS["ASSUR"])


def test_group_findspots_flags_mixed_resolved_and_unresolved_rows_as_conflict():
    config = SITE_CONFIGS["KALHU"]
    rows = (
        MapOdsRow(findspot_id=1, area="D XII"),
        MapOdsRow(findspot_id=1, area="unknown"),
    )
    polygons = (
        MapPolygon(name="D XII", polygon_id="kalhu-d-xii-abc", geometry_checksum="abc"),
    )
    index = index_polygons_by_key(polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)

    groups = group_findspots(rows, derivations)

    assert groups[0].status == "conflict"
    assert groups[0].polygon_id is None


def test_derive_row_preserves_explicit_source_uncertainty():
    config = SITE_CONFIGS["ASSUR"]
    row = MapOdsRow(findspot_id=4392, area="gB4II?")
    polygons = (
        MapPolygon(name="gB4II", polygon_id="assur-gb4ii-abc", geometry_checksum="abc"),
    )

    derivation = derive_row(row, index_polygons_by_key(polygons), config)

    assert derivation.status == "needs-human-curation"
    assert derivation.polygon_id is None
    assert derivation.matched_value == "gB4II?"
