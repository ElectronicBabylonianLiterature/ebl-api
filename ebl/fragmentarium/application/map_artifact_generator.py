from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Collection

from ebl.fragmentarium.application.map_artifact_report import (
    ArtifactReportSummary,
    render_artifact_report,
)
from ebl.fragmentarium.application.map_artifact_storage import publish_artifact_set
from ebl.fragmentarium.application.map_artifact_types import (
    CurationRecord,
    InventoryRecord,
    SiteArtifacts,
)
from ebl.fragmentarium.application.map_curated_mappings import (
    CuratedMappingRecord,
    merge_verified_and_curated,
)
from ebl.fragmentarium.application.map_findspot_grouping import (
    FindspotGroup,
    group_findspots,
)
from ebl.fragmentarium.application.map_mapping_rules import (
    derive_row,
    index_polygons_by_key,
)
from ebl.fragmentarium.application.map_polygon_identity import polygon_match_key
from ebl.fragmentarium.application.map_paths import MAP_DATA_DIR
from ebl.fragmentarium.application.map_site_config import MapSiteConfig
from ebl.fragmentarium.application.map_source_loader import (
    MapOdsRow,
    MapPolygon,
    load_site_ods_rows,
    load_site_polygons,
)

DEFAULT_OUTPUT_DIR = MAP_DATA_DIR
MAX_FINDSPOT_ID = 2**63 - 1


def build_site_artifacts(
    config: MapSiteConfig,
    source_revision: str,
    curated_records_path: Path | None = None,
    ods_rows: tuple[MapOdsRow, ...] | None = None,
    polygons: tuple[MapPolygon, ...] | None = None,
    additional_authoritative_findspot_ids: Collection[int] = (),
) -> SiteArtifacts:
    from ebl.fragmentarium.application.map_curated_mappings import (
        load_curated_mappings,
    )

    revision = source_revision.strip()
    if not revision:
        raise ValueError("sourceRevision must not be blank.")
    rows = ods_rows if ods_rows is not None else load_site_ods_rows(config)
    site_polygons = polygons if polygons is not None else load_site_polygons(config)
    index = index_polygons_by_key(site_polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)
    groups = group_findspots(rows, derivations)

    verified: list[CuratedMappingRecord] = [
        _verified_record(config, group, revision)
        for group in groups
        if group.status == "resolved"
    ]
    known_polygon_ids = {polygon.polygon_id for polygon in site_polygons}
    if any(
        isinstance(findspot_id, bool)
        or not isinstance(findspot_id, int)
        or not 0 <= findspot_id <= MAX_FINDSPOT_ID
        for findspot_id in additional_authoritative_findspot_ids
    ):
        raise ValueError("Additional authoritative findspot IDs must be BSON int64s.")
    source_group_ids = {row.findspot_id for row in rows}
    authoritative_source_findspot_ids = {
        row.findspot_id for row in rows if row.site_name == config.site_name
    }
    authoritative_findspot_ids = authoritative_source_findspot_ids | set(
        additional_authoritative_findspot_ids
    )
    curated = load_curated_mappings(
        curated_records_path,
        config.site_id,
        known_polygon_ids,
        authoritative_findspot_ids,
    )
    mappings = merge_verified_and_curated(tuple(verified), curated)

    curated_ids = {record["findspotId"] for record in curated}
    unresolved_groups = [
        group
        for group in groups
        if group.status == "unresolved" and group.findspot_id not in curated_ids
    ]
    conflict_groups = [
        group
        for group in groups
        if group.status == "conflict" and group.findspot_id not in curated_ids
    ]
    curation = tuple(
        sorted(
            (
                _curation_record(config, group, revision)
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
    summary = ArtifactReportSummary(
        source_row_count=len(rows),
        source_group_count=len(groups),
        verified_mapping_count=len(verified),
        curated_mapping_count=len(curated),
        curated_source_group_count=len(curated_ids & source_group_ids),
        unresolved_row_count=sum(len(group.rows) for group in unresolved_groups),
        unresolved_group_count=len(unresolved_groups),
        conflict_row_count=sum(len(group.rows) for group in conflict_groups),
        conflict_group_count=len(conflict_groups),
        unresolved_labels=Counter(
            _report_label(group.representative_row, config.match_fields)
            for group in unresolved_groups
        ),
    )
    return {
        "inventory": inventory,
        "mappings": mappings,
        "curation": curation,
        "report": render_artifact_report(config, summary),
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


def _report_label(row: MapOdsRow, fields: tuple[str, ...]) -> str:
    values = {"area": row.area, "sector": row.sector, "building": row.building}
    return next((values[field] for field in fields if values[field]), "<blank>")


def _curation_record(
    config: MapSiteConfig, group: FindspotGroup, source_revision: str
) -> CurationRecord:
    row = group.representative_row
    required_decision = (
        "Resolve conflicting polygon matches across duplicate source rows."
        if group.status == "conflict"
        else "Assign a polygon ID or leave the row unresolved."
    )
    return CurationRecord(
        findspotId=group.findspot_id,
        siteId=config.site_id,
        siteName=config.site_name,
        area=row.area,
        sector=row.sector,
        building=row.building,
        map=row.map_name,
        status="needs-human-curation",
        requiredDecision=required_decision,
        polygonIds=[],
        matchMethod="curated",
        reviewer="",
        reviewDate="",
        source="human curation",
        sourceRevision=source_revision,
    )


def write_site_artifacts(
    config: MapSiteConfig,
    output_dir: Path,
    source_revision: str,
    curated_records_path: Path | None = None,
    additional_authoritative_findspot_ids: Collection[int] = (),
) -> SiteArtifacts:
    artifacts = build_site_artifacts(
        config,
        source_revision,
        curated_records_path,
        additional_authoritative_findspot_ids=additional_authoritative_findspot_ids,
    )
    prefix = config.site_id.lower()
    serialized = {
        f"{prefix}_polygon_inventory.json": _serialize_json(artifacts["inventory"]),
        f"{prefix}_findspot_polygon_mappings.json": _serialize_json(
            artifacts["mappings"]
        ),
        f"{prefix}_findspot_polygon_curation_template.json": _serialize_json(
            artifacts["curation"]
        ),
        f"{prefix}_findspot_polygon_curation_report.md": str(artifacts["report"]),
    }
    publish_artifact_set(output_dir, prefix, source_revision, serialized)
    return artifacts


def _serialize_json(payload: object) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
