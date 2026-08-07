from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ebl.fragmentarium.application.map_polygon_identity import (
    normalize_label,
    polygon_match_key,
)
from ebl.fragmentarium.application.map_site_config import MapSiteConfig
from ebl.fragmentarium.application.map_source_loader import MapOdsRow, MapPolygon

MatchStatus = str  # "verified-mapped" | "needs-human-curation"


@dataclass(frozen=True)
class DerivationRecord:
    findspot_id: int
    matched_field: str | None
    matched_value: str
    polygon_id: str | None
    candidate_count: int
    status: MatchStatus


def index_polygons_by_key(
    polygons: tuple[MapPolygon, ...],
) -> dict[str, list[MapPolygon]]:
    index: dict[str, list[MapPolygon]] = defaultdict(list)
    for polygon in polygons:
        key = normalize_label(polygon_match_key(polygon.name))
        index[key].append(polygon)
    return dict(index)


def derive_row(
    row: MapOdsRow, index: dict[str, list[MapPolygon]], config: MapSiteConfig
) -> DerivationRecord:
    field_values = {
        "area": row.area,
        "sector": row.sector,
        "building": row.building,
    }
    for field in config.match_fields:
        value = field_values[field].strip()
        if not value:
            continue
        candidates = index.get(normalize_label(value), [])
        if len(candidates) == 1:
            return DerivationRecord(
                findspot_id=row.findspot_id,
                matched_field=field,
                matched_value=value,
                polygon_id=candidates[0].polygon_id,
                candidate_count=1,
                status="verified-mapped",
            )
        return DerivationRecord(
            findspot_id=row.findspot_id,
            matched_field=field,
            matched_value=value,
            polygon_id=None,
            candidate_count=len(candidates),
            status="needs-human-curation",
        )
    return DerivationRecord(
        findspot_id=row.findspot_id,
        matched_field=None,
        matched_value="",
        polygon_id=None,
        candidate_count=0,
        status="needs-human-curation",
    )
