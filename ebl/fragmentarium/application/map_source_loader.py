from __future__ import annotations

from dataclasses import dataclass

from ebl.fragmentarium.application.map_geometry import (
    assert_plausible_geographic_bounds,
    reproject_rings,
    strict_zip,
)
from ebl.fragmentarium.application.map_ods_reader import read_ods_rows
from ebl.fragmentarium.application.map_polygon_identity import build_polygon_id
from ebl.fragmentarium.application.map_site_config import (
    CRS_SIGNATURES,
    MapSiteConfig,
    ODS_COLUMN_TO_FIELD,
)
from ebl.fragmentarium.application.map_source_reader import (
    load_dbf_encoding,
    load_dbf_rows,
    load_prj_wkt,
    load_shp_polygon_rings,
)


@dataclass(frozen=True)
class MapOdsRow:
    findspot_id: int
    site_name: str = ""
    sector: str = ""
    area: str = ""
    building: str = ""
    map_name: str = ""


@dataclass(frozen=True)
class MapPolygon:
    name: str
    polygon_id: str
    geometry_checksum: str


def load_site_ods_rows(config: MapSiteConfig) -> tuple[MapOdsRow, ...]:
    raw_rows = read_ods_rows(config.ods_path)
    if not raw_rows:
        raise ValueError(f"{config.ods_path} contains no rows.")
    header = raw_rows[0][: len(config.ods_header)]
    if tuple(header) != config.ods_header:
        raise ValueError(f"Unexpected ODS header in {config.ods_path}: {header!r}")
    field_positions = [
        (ODS_COLUMN_TO_FIELD[column], index)
        for index, column in enumerate(config.ods_header)
        if ODS_COLUMN_TO_FIELD[column] is not None
    ]
    rows = []
    for values in raw_rows[1:]:
        if not values or not values[0].strip():
            continue
        text_fields: dict[str, str] = {
            field: (values[index].strip() if index < len(values) else "")
            for field, index in field_positions
        }
        findspot_id = int(text_fields.pop("findspot_id"))
        rows.append(MapOdsRow(findspot_id=findspot_id, **text_fields))
    return tuple(rows)


def load_site_polygons(config: MapSiteConfig) -> tuple[MapPolygon, ...]:
    encoding = load_dbf_encoding(config.shp_base.with_suffix(".cpg"))
    attributes = load_dbf_rows(config.shp_base.with_suffix(".dbf"), encoding)
    geometry_rows = load_shp_polygon_rings(config.shp_base.with_suffix(".shp"))
    prj = load_prj_wkt(config.shp_base.with_suffix(".prj"))
    if CRS_SIGNATURES[config.crs_kind] not in prj:
        raise ValueError(
            f"{config.site_id} shapefile CRS does not match expected "
            f"{config.crs_kind} signature."
        )
    if len(attributes) != len(geometry_rows):
        raise ValueError(
            f"{config.site_id} shapefile geometry and DBF row counts differ."
        )
    polygons = tuple(
        _build_polygon(config, attribute["Name"], rings)
        for attribute, rings in strict_zip(attributes, geometry_rows)
    )
    if len({polygon.polygon_id for polygon in polygons}) != len(polygons):
        raise ValueError(f"{config.site_id} polygon IDs must be unique.")
    return polygons


def _build_polygon(config: MapSiteConfig, name: str, rings) -> MapPolygon:
    canonical_rings = (
        reproject_rings(rings, config.source_crs)
        if config.requires_reprojection
        else rings
    )
    if config.requires_reprojection:
        assert_plausible_geographic_bounds(canonical_rings)
    polygon_id, checksum = build_polygon_id(
        config.polygon_id_prefix, name, canonical_rings
    )
    return MapPolygon(name=name, polygon_id=polygon_id, geometry_checksum=checksum)
