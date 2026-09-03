from dataclasses import replace

import pytest

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
)


def test_load_site_ods_rows_rejects_unexpected_header():
    config = replace(SITE_CONFIGS["ASSUR"], ods_header=("site", "_id", "area"))

    with pytest.raises(ValueError, match="Unexpected ODS header"):
        load_site_ods_rows(config)


def test_load_site_ods_rows_skips_blank_id_rows():
    rows = load_site_ods_rows(SITE_CONFIGS["ASSUR"])

    assert all(row.findspot_id for row in rows)


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
