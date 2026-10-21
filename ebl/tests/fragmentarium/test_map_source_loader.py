from dataclasses import replace

import pytest

import ebl.fragmentarium.application.map_source_loader as source_loader

from ebl.fragmentarium.application.map_findspot_grouping import group_findspots
from ebl.fragmentarium.application.map_mapping_rules import (
    derive_row,
    index_polygons_by_key,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS


def test_load_site_ods_rows_rejects_unexpected_header():
    config = replace(SITE_CONFIGS["ASSUR"], ods_header=("site", "_id", "area"))

    with pytest.raises(ValueError, match="Unexpected ODS header"):
        source_loader.load_site_ods_rows(config)


def test_load_site_ods_rows_skips_blank_id_rows():
    rows = source_loader.load_site_ods_rows(SITE_CONFIGS["ASSUR"])

    assert all(row.findspot_id for row in rows)


def test_load_site_ods_rows_rejects_empty_source(monkeypatch):
    monkeypatch.setattr(source_loader, "read_ods_rows", lambda path: ())

    with pytest.raises(ValueError, match="contains no rows"):
        source_loader.load_site_ods_rows(SITE_CONFIGS["ASSUR"])


@pytest.mark.parametrize(
    "names, geometry_count, crs, message",
    [
        (("A",), 1, "invalid CRS", "does not match"),
        (("A", "B"), 1, 'GEOGCS["GCS_WGS_1984"', "row counts differ"),
        (("A", "A"), 2, 'GEOGCS["GCS_WGS_1984"', "must be unique"),
    ],
)
def test_load_site_polygons_rejects_inconsistent_sources(
    monkeypatch, names, geometry_count, crs, message
):
    ring = ((43.0, 35.0), (43.0, 35.1), (43.1, 35.1), (43.0, 35.0))
    monkeypatch.setattr(source_loader, "load_dbf_encoding", lambda path: "UTF-8")
    monkeypatch.setattr(
        source_loader,
        "load_dbf_rows",
        lambda path, encoding: tuple({"Name": name} for name in names),
    )
    monkeypatch.setattr(
        source_loader,
        "load_shp_polygon_rings",
        lambda path: tuple((ring,) for _ in range(geometry_count)),
    )
    monkeypatch.setattr(source_loader, "load_prj_wkt", lambda path: crs)

    with pytest.raises(ValueError, match=message):
        source_loader.load_site_polygons(SITE_CONFIGS["ASSUR"])


def test_group_findspots_deduplicates_agreeing_progressive_rows():
    config = SITE_CONFIGS["KALHU"]
    rows = (
        source_loader.MapOdsRow(findspot_id=1, area="D XII"),
        source_loader.MapOdsRow(findspot_id=1, area="D XII"),
    )
    polygons = (
        source_loader.MapPolygon(
            name="D XII", polygon_id="kalhu-d-xii-abc", geometry_checksum="abc"
        ),
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
        source_loader.MapOdsRow(findspot_id=1, area="D XII"),
        source_loader.MapOdsRow(findspot_id=1, area="ZT"),
    )
    polygons = (
        source_loader.MapPolygon(
            name="D XII", polygon_id="kalhu-d-xii-abc", geometry_checksum="abc"
        ),
        source_loader.MapPolygon(
            name="ZT", polygon_id="kalhu-zt-def", geometry_checksum="def"
        ),
    )
    index = index_polygons_by_key(polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)

    groups = group_findspots(rows, derivations)

    assert len(groups) == 1
    assert groups[0].status == "conflict"
    assert groups[0].polygon_id is None
