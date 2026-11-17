from __future__ import annotations

from scripts.maps.map_artifact_records import (
    build_verified_record,
    build_curation_record,
)
from collections import Counter
import json
from pathlib import Path
from typing import Collection

from scripts.maps.map_artifact_report import (
    ArtifactReportSummary,
    render_artifact_report,
)
from ebl.fragmentarium.application.map_artifact_storage import publish_artifact_set
from scripts.maps.map_artifact_types import (
    InventoryRecord,
    SiteArtifacts,
)
from scripts.maps.map_curated_mappings import (
    CuratedMappingRecord,
    load_curated_mappings,
    merge_verified_and_curated,
)
from scripts.maps.map_findspot_grouping import (
    group_findspots,
)
from scripts.maps.map_mapping_rules import (
    derive_row,
    index_polygons_by_key,
)
from scripts.maps.map_polygon_identity import polygon_match_key
from ebl.fragmentarium.application.map_json import is_bson_int64
from scripts.maps.map_membership import load_membership_evidence
from ebl.fragmentarium.application.map_paths import MAP_DATA_DIR
from scripts.maps.map_site_config import MapSiteConfig
from scripts.maps.map_source_loader import (
    MapOdsRow,
    SiteSources,
    load_site_ods_rows,
    load_site_polygons,
)

DEFAULT_OUTPUT_DIR = MAP_DATA_DIR


def build_site_artifacts(
    config: MapSiteConfig,
    source_revision: str,
    curated_records_path: Path | None = None,
    sources: SiteSources | None = None,
    additional_authoritative_findspot_ids: Collection[int] = (),
) -> SiteArtifacts:
    revision = source_revision.strip()
    if not revision:
        raise ValueError("sourceRevision must not be blank.")
    sources = sources or SiteSources()
    rows = (
        sources.ods_rows if sources.ods_rows is not None else load_site_ods_rows(config)
    )
    site_polygons = (
        sources.polygons if sources.polygons is not None else load_site_polygons(config)
    )
    index = index_polygons_by_key(site_polygons)
    derivations = tuple(derive_row(row, index, config) for row in rows)
    evidence = sources.membership_evidence or load_membership_evidence()
    authoritative_findspot_ids = evidence.findspot_ids_for(config.site_name)
    groups = group_findspots(rows, derivations)

    verified: list[CuratedMappingRecord] = [
        build_verified_record(config, group, revision)
        for group in groups
        if group.status == "resolved"
        and group.findspot_id in authoritative_findspot_ids
    ]
    known_polygon_ids = {polygon.polygon_id for polygon in site_polygons}
    if any(
        not is_bson_int64(findspot_id)
        for findspot_id in additional_authoritative_findspot_ids
    ):
        raise ValueError("Additional authoritative findspot IDs must be BSON int64s.")
    source_group_ids = {row.findspot_id for row in rows}
    if not set(additional_authoritative_findspot_ids) <= authoritative_findspot_ids:
        raise ValueError(
            "Additional findspot IDs lack authoritative membership evidence."
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
        if (
            group.status == "unresolved"
            or (
                group.status == "resolved"
                and group.findspot_id not in authoritative_findspot_ids
            )
        )
        and group.findspot_id not in curated_ids
    ]
    conflict_groups = [
        group
        for group in groups
        if group.status == "conflict" and group.findspot_id not in curated_ids
    ]
    curation = tuple(
        sorted(
            (
                build_curation_record(
                    config,
                    group,
                    revision,
                    group.findspot_id in authoritative_findspot_ids,
                )
                for group in groups
                if (
                    group.status != "resolved"
                    or group.findspot_id not in authoritative_findspot_ids
                )
                and group.findspot_id not in curated_ids
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
        membership_source_revision=evidence.source_revision,
    )
    return {
        "inventory": inventory,
        "mappings": mappings,
        "curation": curation,
        "report": render_artifact_report(config, summary),
        "derivations": derivations,
    }


def _report_label(row: MapOdsRow, fields: tuple[str, ...]) -> str:
    values = {"area": row.area, "sector": row.sector, "building": row.building}
    return next((values[field] for field in fields if values[field]), "<blank>")


def write_site_artifacts(
    config: MapSiteConfig,
    output_dir: Path,
    source_revision: str,
    curated_records_path: Path | None = None,
    additional_authoritative_findspot_ids: Collection[int] = (),
) -> SiteArtifacts:
    prefix = config.site_id.lower()
    if curated_records_path is not None:
        for suffix in (
            "polygon_inventory.json",
            "findspot_polygon_mappings.json",
            "findspot_polygon_curation_template.json",
            "findspot_polygon_curation_report.json",
            "artifact_manifest.json",
        ):
            target = output_dir / f"{prefix}_{suffix}"
            if curated_records_path.resolve() == target.resolve() or (
                curated_records_path.exists()
                and target.exists()
                and curated_records_path.samefile(target)
            ):
                raise ValueError(
                    "Reviewed curation input must not alias a publication target. "
                    "Save it separately before generating artifacts."
                )
    artifacts = build_site_artifacts(
        config,
        source_revision,
        curated_records_path,
        additional_authoritative_findspot_ids=additional_authoritative_findspot_ids,
    )
    serialized = {
        f"{prefix}_polygon_inventory.json": _serialize_json(artifacts["inventory"]),
        f"{prefix}_findspot_polygon_mappings.json": _serialize_json(
            artifacts["mappings"]
        ),
        f"{prefix}_findspot_polygon_curation_template.json": _serialize_json(
            artifacts["curation"]
        ),
        f"{prefix}_findspot_polygon_curation_report.json": str(artifacts["report"]),
    }
    publish_artifact_set(output_dir, prefix, source_revision, serialized)
    return artifacts


def _serialize_json(payload: object) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
