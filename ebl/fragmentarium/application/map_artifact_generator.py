from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import TypedDict

from ebl.fragmentarium.application.map_curated_mappings import (
    CuratedMappingRecord,
    merge_verified_and_curated,
)
from ebl.fragmentarium.application.map_findspot_grouping import (
    FindspotGroup,
    group_findspots,
)
from ebl.fragmentarium.application.map_mapping_rules import (
    DerivationRecord,
    derive_row,
    index_polygons_by_key,
)
from ebl.fragmentarium.application.map_polygon_identity import polygon_match_key
from ebl.fragmentarium.application.map_site_config import MapSiteConfig
from ebl.fragmentarium.application.map_source_loader import (
    MapOdsRow,
    MapPolygon,
    load_site_ods_rows,
    load_site_polygons,
)

DEFAULT_OUTPUT_DIR = Path("ebl/fragmentarium/data/map")


class InventoryRecord(TypedDict):
    polygonId: str
    name: str
    areaName: str
    siteId: str
    siteName: str
    geometryChecksum: str


class CurationRecord(TypedDict):
    findspotId: int
    siteId: str
    siteName: str
    area: str
    sector: str
    map: str
    status: str
    requiredDecision: str


class SiteArtifacts(TypedDict):
    inventory: tuple[InventoryRecord, ...]
    mappings: tuple[CuratedMappingRecord, ...]
    curation: tuple[CurationRecord, ...]
    report: str
    derivations: tuple[DerivationRecord, ...]


def build_site_artifacts(
    config: MapSiteConfig,
    source_revision: str,
    curated_records_path: Path | None = None,
    ods_rows: tuple[MapOdsRow, ...] | None = None,
    polygons: tuple[MapPolygon, ...] | None = None,
) -> SiteArtifacts:
    from ebl.fragmentarium.application.map_curated_mappings import (
        load_curated_mappings,
    )

    rows = ods_rows if ods_rows is not None else load_site_ods_rows(config)
    site_polygons = polygons if polygons is not None else load_site_polygons(config)
    index = index_polygons_by_key(site_polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)
    groups = group_findspots(rows, derivations)

    verified: list[CuratedMappingRecord] = [
        _verified_record(config, group, source_revision)
        for group in groups
        if group.status == "resolved"
    ]
    known_polygon_ids = {polygon.polygon_id for polygon in site_polygons}
    curated = load_curated_mappings(
        curated_records_path, config.site_id, known_polygon_ids
    )
    mappings = merge_verified_and_curated(tuple(verified), curated)

    curated_ids = {record["findspotId"] for record in curated}
    conflicts = [group for group in groups if group.status == "conflict"]
    curation = tuple(
        sorted(
            (
                _curation_record(config, group)
                for group in groups
                if group.status != "resolved" and group.findspot_id not in curated_ids
            ),
            key=lambda item: int(item["findspotId"]),
        )
    )
    inventory = tuple(
        InventoryRecord(
            polygonId=polygon.polygon_id,
            name=polygon.name,
            areaName=polygon_match_key(polygon.name),
            siteId=config.site_id,
            siteName=config.site_name,
            geometryChecksum=polygon.geometry_checksum,
        )
        for polygon in sorted(site_polygons, key=lambda item: item.polygon_id)
    )
    primary_field = config.match_fields[0]
    unresolved = Counter(
        _primary_field_value(group.representative_row, primary_field) or "<blank>"
        for group in groups
        if group.status == "unresolved" and group.findspot_id not in curated_ids
    )
    return {
        "inventory": inventory,
        "mappings": mappings,
        "curation": curation,
        "report": _render_report(
            config,
            len(verified),
            len(curated),
            len(conflicts),
            len(curation),
            unresolved,
        ),
        "derivations": derivations,
    }


def _verified_record(
    config: MapSiteConfig, group: FindspotGroup, source_revision: str
) -> CuratedMappingRecord:
    polygon_id = group.polygon_id
    assert polygon_id is not None
    return {
        "findspotId": group.findspot_id,
        "polygonIds": [polygon_id],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": config.source_label,
        "sourceRevision": source_revision,
    }


def _primary_field_value(row: MapOdsRow, field: str) -> str:
    return {"area": row.area, "sector": row.sector, "building": row.building}[field]


def _curation_record(config: MapSiteConfig, group: FindspotGroup) -> CurationRecord:
    row = group.representative_row
    required_decision = (
        "Resolve conflicting polygon matches across duplicate source rows."
        if group.status == "conflict"
        else "Assign a polygon ID or confirm the row is unmapped."
    )
    return CurationRecord(
        findspotId=group.findspot_id,
        siteId=config.site_id,
        siteName=config.site_name,
        area=row.area,
        sector=row.sector,
        map=row.map_name,
        status="needs-human-curation",
        requiredDecision=required_decision,
    )


def write_site_artifacts(
    config: MapSiteConfig,
    output_dir: Path,
    source_revision: str,
    curated_records_path: Path | None = None,
) -> SiteArtifacts:
    artifacts = build_site_artifacts(config, source_revision, curated_records_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = config.site_id.lower()
    _atomic_write_json(
        output_dir / f"{prefix}_polygon_inventory.json", artifacts["inventory"]
    )
    _atomic_write_json(
        output_dir / f"{prefix}_findspot_polygon_mappings.json", artifacts["mappings"]
    )
    _atomic_write_json(
        output_dir / f"{prefix}_findspot_polygon_curation_template.json",
        artifacts["curation"],
    )
    _atomic_write_text(
        output_dir / f"{prefix}_findspot_polygon_curation_report.md",
        str(artifacts["report"]),
    )
    return artifacts


def _render_report(
    config: MapSiteConfig,
    verified_count: int,
    curated_count: int,
    conflicts_count: int,
    unresolved_total: int,
    unresolved: Counter[str],
) -> str:
    lines = [
        config.report_title,
        "",
        "- Generated from immutable ODS and shapefile sources.",
        f"- Verified mappings: {verified_count}",
        *([f"- Curated mappings: {curated_count}"] if curated_count else []),
        f"- Unresolved rows: {unresolved_total}",
        f"- Source conflicts: {conflicts_count}",
        "- Invalid source rows: 0",
        "",
        "## Deterministic rule used",
        "",
        f"`{config.derivation_rule_text}`",
        "",
        "Normalization applies Unicode NFKC, trims whitespace, removes `?`, and case-folds both sides.",
        "",
        "## Human decision required",
        "",
        "The remaining rows need scholarly curation because no unique deterministic polygon match exists.",
        "",
        config.unresolved_heading,
        "",
    ]
    lines.extend(f"- `{label}`: {count}" for label, count in sorted(unresolved.items()))
    return "\n".join(lines) + "\n"


def _atomic_write_json(path: Path, payload: object) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
