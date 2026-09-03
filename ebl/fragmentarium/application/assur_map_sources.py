from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ebl.fragmentarium.application.map_polygon_identity import (
    build_polygon_id,
    normalize_label,
    polygon_match_key,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.application.map_source_loader import (
    MapOdsRow as AssurOdsRow,
    MapPolygon as AssurPolygon,
    load_site_ods_rows,
    load_site_polygons,
)

_ASSUR_CONFIG = SITE_CONFIGS["ASSUR"]
ASSUR_ODS_PATH = _ASSUR_CONFIG.ods_path
ASSUR_SHP_BASE = _ASSUR_CONFIG.shp_base
ASSUR_SITE_ID = _ASSUR_CONFIG.site_id
ASSUR_SITE_NAME = _ASSUR_CONFIG.site_name

__all__ = [
    "AssurOdsRow",
    "AssurPolygon",
    "ASSUR_ODS_PATH",
    "ASSUR_SHP_BASE",
    "ASSUR_SITE_ID",
    "ASSUR_SITE_NAME",
    "load_assur_ods_rows",
    "load_assur_polygons",
    "normalize_assur_area_label",
    "shapefile_area_name",
    "build_assur_polygon_id",
]


def load_assur_ods_rows(path: Path = ASSUR_ODS_PATH) -> tuple[AssurOdsRow, ...]:
    config = (
        _ASSUR_CONFIG
        if path == ASSUR_ODS_PATH
        else replace(_ASSUR_CONFIG, ods_path=path)
    )
    return load_site_ods_rows(config)


def load_assur_polygons(base_path: Path = ASSUR_SHP_BASE) -> tuple[AssurPolygon, ...]:
    config = (
        _ASSUR_CONFIG
        if base_path == ASSUR_SHP_BASE
        else replace(_ASSUR_CONFIG, shp_base=base_path)
    )
    return load_site_polygons(config)


def normalize_assur_area_label(value: str) -> str:
    return normalize_label(value)


def shapefile_area_name(name: str) -> str:
    return polygon_match_key(name)


def build_assur_polygon_id(
    name: str, rings: tuple[tuple[tuple[float, float], ...], ...]
) -> tuple[str, str]:
    return build_polygon_id("assur", name, rings)
