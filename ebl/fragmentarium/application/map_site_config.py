from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CrsKind = Literal["geographic-wgs84", "web-mercator-wgs84"]

_GEOGRAPHIC_WGS84_SIGNATURE = 'GEOGCS["GCS_WGS_1984"'
_WEB_MERCATOR_WGS84_SIGNATURE = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere"'

CRS_SIGNATURES: dict[CrsKind, str] = {
    "geographic-wgs84": _GEOGRAPHIC_WGS84_SIGNATURE,
    "web-mercator-wgs84": _WEB_MERCATOR_WGS84_SIGNATURE,
}
CRS_EPSG: dict[CrsKind, str] = {
    "geographic-wgs84": "EPSG:4326",
    "web-mercator-wgs84": "EPSG:3857",
}

# Column tokens as they appear (in order) in each site's ODS header, mapped to
# the corresponding MapOdsRow field name. An empty token marks a blank spacer
# column present in the raw source file that carries no data.
ODS_COLUMN_TO_FIELD = {
    "_id": "findspot_id",
    "site": "site_name",
    "sector": "sector",
    "area": "area",
    "building": "building",
    "map": "map_name",
    "": None,
}


@dataclass(frozen=True)
class MapSiteConfig:
    site_id: str
    site_name: str
    shp_base: Path
    ods_path: Path
    ods_header: tuple[str, ...]
    crs_kind: CrsKind
    polygon_id_prefix: str
    match_fields: tuple[str, ...]
    source_label: str
    report_title: str
    derivation_rule_text: str
    unresolved_heading: str = "Unresolved primary-field values:"

    def __post_init__(self) -> None:
        unknown_columns = set(self.ods_header) - set(ODS_COLUMN_TO_FIELD)
        if unknown_columns:
            raise ValueError(f"Unknown ODS columns in site config: {unknown_columns}")
        unknown_fields = set(self.match_fields) - {
            "area",
            "sector",
            "building",
        }
        if unknown_fields:
            raise ValueError(f"Unknown match fields in site config: {unknown_fields}")

    @property
    def requires_reprojection(self) -> bool:
        return self.crs_kind != "geographic-wgs84"

    @property
    def source_crs(self) -> str:
        return CRS_EPSG[self.crs_kind]


SITE_CONFIGS: dict[str, MapSiteConfig] = {
    "ASSUR": MapSiteConfig(
        site_id="ASSUR",
        site_name="Aššur",
        shp_base=Path("Maps/Assur LRZ/Findspots/Findspots"),
        ods_path=Path("Maps/Assur LRZ/Assur Tafeln.ods"),
        ods_header=("_id", "area", "sector", "site", "map"),
        crs_kind="geographic-wgs84",
        polygon_id_prefix="assur",
        match_fields=("area",),
        source_label="Assur Tafeln.ods",
        report_title="# Aššur Map Curation Report",
        derivation_rule_text=(
            "normalize(ODS.area) == normalize(shapefile.Name without leading digits)"
        ),
        unresolved_heading="Unresolved area labels:",
    ),
    "URUK": MapSiteConfig(
        site_id="URUK",
        site_name="Uruk",
        shp_base=Path("Maps/Uruk LRZ/Findspots/Findspots"),
        ods_path=Path("Maps/Uruk Tafeln aktualisiert 24-07-25.ods"),
        ods_header=("_id", "site", "sector", "area", "building", "map"),
        crs_kind="geographic-wgs84",
        polygon_id_prefix="uruk",
        match_fields=("area",),
        source_label="Uruk Tafeln aktualisiert 24-07-25.ods",
        report_title="# Uruk Map Curation Report",
        derivation_rule_text=(
            "normalize(ODS.area) == normalize(shapefile.Name without leading digits)"
        ),
        unresolved_heading="Unresolved area labels:",
    ),
    "KALHU": MapSiteConfig(
        site_id="KALHU",
        site_name="Kalḫu",
        shp_base=Path("Maps/Kalhu LRZ/Findspots/Findspots"),
        ods_path=Path("Maps/Kalhu LRZ/Kalhu Tafeln.ods"),
        ods_header=("_id", "site", "sector", "area", "building", "", "map"),
        crs_kind="web-mercator-wgs84",
        polygon_id_prefix="kalhu",
        match_fields=("area", "building"),
        source_label="Kalhu Tafeln.ods",
        report_title="# Kalḫu Map Curation Report",
        derivation_rule_text=(
            "normalize(ODS.area) == normalize(shapefile.Name without leading digits); "
            "when area is blank, fall back to "
            "normalize(ODS.building) == normalize(shapefile.Name without leading digits)"
        ),
        unresolved_heading="Unresolved area/building values:",
    ),
    "NIPPUR": MapSiteConfig(
        site_id="NIPPUR",
        site_name="Nippur",
        shp_base=Path("Maps/Nippur LRZ/Findspots/Findspots"),
        ods_path=Path("Maps/Nippur LRZ/Nippur Tafeln.ods"),
        ods_header=("_id", "site", "sector", "area", "building", "map"),
        crs_kind="web-mercator-wgs84",
        polygon_id_prefix="nippur",
        match_fields=("area", "sector"),
        source_label="Nippur Tafeln.ods",
        report_title="# Nippur Map Curation Report",
        derivation_rule_text=(
            "normalize(ODS.area) == normalize(shapefile.Name without leading digits); "
            "when area is blank, fall back to "
            "normalize(ODS.sector) == normalize(shapefile.Name without leading digits). "
            "Historical map plate references (the ODS `map` column) are never used as "
            "polygon identifiers."
        ),
        unresolved_heading="Unresolved area/sector values:",
    ),
}
