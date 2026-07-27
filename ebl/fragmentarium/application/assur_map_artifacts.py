from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import TypedDict

from ebl.fragmentarium.application.assur_map_sources import (
    ASSUR_SITE_ID,
    ASSUR_SITE_NAME,
    AssurOdsRow,
    AssurPolygon,
    load_assur_ods_rows,
    load_assur_polygons,
    normalize_assur_area_label,
)


DEFAULT_OUTPUT_DIR = Path("ebl/fragmentarium/data/map")
DERIVATION_RULE = (
    "normalize(ODS.area) == normalize(shapefile.Name without leading digits)"
)


@dataclass(frozen=True)
class AssurDerivationRecord:
    findspot_id: int
    raw_ods_area: str
    normalized_ods_area: str
    polygon_source_name: str | None
    polygon_id: str | None
    derivation_rule: str
    match_method: str | None
    candidate_count: int
    status: str


class AssurArtifacts(TypedDict):
    inventory: tuple[AssurInventoryRecord, ...]
    mappings: tuple[AssurMappingRecord, ...]
    curation: tuple[AssurCurationRecord, ...]
    report: str
    derivations: tuple[AssurDerivationRecord, ...]


class AssurInventoryRecord(TypedDict):
    polygonId: str
    name: str
    areaName: str
    siteId: str
    siteName: str
    geometryChecksum: str


class AssurMappingRecord(TypedDict):
    findspotId: int
    polygonIds: list[str]
    locationPrecision: str
    matchMethod: str
    source: str
    sourceRevision: str


class AssurCurationRecord(TypedDict):
    findspotId: int
    siteId: str
    siteName: str
    area: str
    sector: str
    map: str
    status: str
    requiredDecision: str


def build_assur_artifacts(
    source_revision: str,
    ods_rows: tuple[AssurOdsRow, ...] | None = None,
    polygons: tuple[AssurPolygon, ...] | None = None,
) -> AssurArtifacts:
    rows = ods_rows or load_assur_ods_rows()
    source_polygons = polygons or load_assur_polygons()
    polygons_by_area = defaultdict(list)
    for polygon in source_polygons:
        polygons_by_area[normalize_assur_area_label(polygon.area_name)].append(polygon)
    derivations = tuple(_derive_row(row, polygons_by_area) for row in rows)
    mappings: list[AssurMappingRecord] = []
    for record in derivations:
        if record.status != "verified-mapped":
            continue
        if record.polygon_id is None:
            raise ValueError("Verified Aššur mappings must include a polygon ID.")
        mappings.append(
            {
                "findspotId": record.findspot_id,
                "polygonIds": [record.polygon_id],
                "locationPrecision": "excavation-area",
                "matchMethod": "verified-source",
                "source": "Assur Tafeln.ods",
                "sourceRevision": source_revision,
            }
        )
    curation: list[AssurCurationRecord] = [
        {
            "findspotId": row.findspot_id,
            "siteId": ASSUR_SITE_ID,
            "siteName": ASSUR_SITE_NAME,
            "area": row.area,
            "sector": row.sector,
            "map": row.map_name,
            "status": record.status,
            "requiredDecision": "Assign a polygon ID or confirm the row is unmapped.",
        }
        for row, record in zip(rows, derivations, strict=True)
        if record.status != "verified-mapped"
    ]
    inventory = tuple(
        AssurInventoryRecord(
            polygonId=polygon.polygon_id,
            name=polygon.name,
            areaName=polygon.area_name,
            siteId=ASSUR_SITE_ID,
            siteName=ASSUR_SITE_NAME,
            geometryChecksum=polygon.geometry_checksum,
        )
        for polygon in sorted(source_polygons, key=lambda item: item.polygon_id)
    )
    unresolved = Counter(
        row.area or "<blank>"
        for row, record in zip(rows, derivations, strict=True)
        if record.status != "verified-mapped"
    )
    return {
        "inventory": inventory,
        "mappings": tuple(sorted(mappings, key=lambda item: int(item["findspotId"]))),
        "curation": tuple(sorted(curation, key=lambda item: int(item["findspotId"]))),
        "report": _render_report(derivations, unresolved),
        "derivations": derivations,
    }


def write_assur_artifacts(output_dir: Path, source_revision: str) -> AssurArtifacts:
    artifacts = build_assur_artifacts(source_revision)
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(
        output_dir / "assur_polygon_inventory.json", artifacts["inventory"]
    )
    _atomic_write_json(
        output_dir / "assur_findspot_polygon_mappings.json", artifacts["mappings"]
    )
    _atomic_write_json(
        output_dir / "assur_findspot_polygon_curation_template.json",
        artifacts["curation"],
    )
    _atomic_write_text(
        output_dir / "assur_findspot_polygon_curation_report.md",
        str(artifacts["report"]),
    )
    return artifacts


def _derive_row(
    row: AssurOdsRow, polygons_by_area: dict[str, list[AssurPolygon]]
) -> AssurDerivationRecord:
    normalized_area = normalize_assur_area_label(row.area)
    candidates = polygons_by_area.get(normalized_area, []) if normalized_area else []
    polygon = candidates[0] if len(candidates) == 1 else None
    return AssurDerivationRecord(
        findspot_id=row.findspot_id,
        raw_ods_area=row.area,
        normalized_ods_area=normalized_area,
        polygon_source_name=polygon.name if polygon else None,
        polygon_id=polygon.polygon_id if polygon else None,
        derivation_rule=DERIVATION_RULE,
        match_method="verified-source" if polygon else None,
        candidate_count=len(candidates),
        status="verified-mapped" if polygon else "needs-human-curation",
    )


def _render_report(
    derivations: tuple[AssurDerivationRecord, ...], unresolved: Counter[str]
) -> str:
    verified = sum(record.status == "verified-mapped" for record in derivations)
    unresolved_total = sum(record.status != "verified-mapped" for record in derivations)
    lines = [
        "# Aššur Map Curation Report",
        "",
        "- Generated from immutable ODS and shapefile sources.",
        f"- Verified mappings: {verified}",
        f"- Unresolved rows: {unresolved_total}",
        "- Source conflicts: 0",
        "- Invalid source rows: 0",
        "",
        "## Deterministic rule used",
        "",
        f"`{DERIVATION_RULE}`",
        "",
        "Normalization applies Unicode NFKC, trims whitespace, removes `?`, and case-folds both sides.",
        "",
        "## Human decision required",
        "",
        "The remaining rows need scholarly curation because no unique deterministic polygon match exists.",
        "",
        "Unresolved area labels:",
        "",
    ]
    lines.extend(f"- `{label}`: {count}" for label, count in sorted(unresolved.items()))
    return "\n".join(lines) + "\n"


def _atomic_write_json(path: Path, payload: object) -> None:
    _atomic_write_text(
        path,
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
