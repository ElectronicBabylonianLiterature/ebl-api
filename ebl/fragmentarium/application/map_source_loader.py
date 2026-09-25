from __future__ import annotations

from dataclasses import dataclass

from ebl.fragmentarium.application.map_geometry import (
    assert_plausible_geographic_bounds,
    reproject_geometry,
    strict_zip,
)
from ebl.fragmentarium.application.map_ods_reader import read_ods_rows
from ebl.fragmentarium.application.map_polygon_identity import build_polygon_id
from ebl.fragmentarium.application.map_site_config import (
    MapSiteConfig,
    ODS_COLUMN_TO_FIELD,
)
from ebl.fragmentarium.application.map_source_reader import (
    load_dbf_encoding,
    load_dbf_rows,
    load_prj_wkt,
    load_shp_polygon_geometries,
)

MAX_FINDSPOT_ID = 2**63 - 1


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
        raw_findspot_id = text_fields.pop("findspot_id")
        if (
            not raw_findspot_id.isascii()
            or not raw_findspot_id.isdecimal()
            or int(raw_findspot_id) > MAX_FINDSPOT_ID
        ):
            raise ValueError(
                f"Invalid findspot ID {raw_findspot_id!r} in {config.ods_path}."
            )
        findspot_id = int(raw_findspot_id)
        rows.append(MapOdsRow(findspot_id=findspot_id, **text_fields))
    return tuple(rows)


def load_site_polygons(config: MapSiteConfig) -> tuple[MapPolygon, ...]:
    encoding = load_dbf_encoding(config.shp_base.with_suffix(".cpg"))
    attributes = load_dbf_rows(config.shp_base.with_suffix(".dbf"), encoding)
    geometry_rows = load_shp_polygon_geometries(config.shp_base.with_suffix(".shp"))
    prj = load_prj_wkt(config.shp_base.with_suffix(".prj"))
    from pyproj import CRS
    from pyproj.exceptions import CRSError

    try:
        source_crs = CRS.from_wkt(prj)
    except CRSError as error:
        raise ValueError(f"{config.site_id} shapefile CRS is invalid.") from error
    expected_crs = CRS.from_user_input(config.source_crs)
    if not source_crs.equals(expected_crs, ignore_axis_order=True):
        raise ValueError(
            f"{config.site_id} shapefile CRS does not match expected {config.source_crs}."
        )
    if len(attributes) != len(geometry_rows):
        raise ValueError(
            f"{config.site_id} shapefile geometry and DBF row counts differ."
        )
    polygons = tuple(
        _build_polygon(config, attribute["Name"], geometry, source_crs)
        for attribute, geometry in strict_zip(attributes, geometry_rows)
    )
    if len({polygon.polygon_id for polygon in polygons}) != len(polygons):
        raise ValueError(f"{config.site_id} polygon IDs must be unique.")
    return polygons


def _build_polygon(
    config: MapSiteConfig, name: str, geometry, source_crs=None
) -> MapPolygon:
    canonical_geometry = (
        reproject_geometry(geometry, source_crs or config.source_crs)
        if config.requires_reprojection
        else geometry
    )
    assert_plausible_geographic_bounds(canonical_geometry)
    polygon_id, checksum = build_polygon_id(
        config.polygon_id_prefix, name, canonical_geometry
    )
    return MapPolygon(name=name, polygon_id=polygon_id, geometry_checksum=checksum)
