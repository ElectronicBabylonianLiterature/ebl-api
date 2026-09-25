from __future__ import annotations

import hashlib
from pathlib import Path
import re

from ebl.common.query.parameter_parser import MAX_FINDSPOT_ID
from ebl.fragmentarium.application.map_artifact_storage import (
    artifact_directory_lock,
    artifact_manifest_name,
)
from ebl.fragmentarium.application.map_artifact_types import (
    CurationRecord,
    InventoryRecord,
)
from ebl.fragmentarium.application.map_curated_mappings import CuratedMappingRecord
from ebl.fragmentarium.application.map_json import load_strict_json
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.fragmentarium.application.map_polygon_identity import (
    contains_control_character,
    polygon_match_key,
    slugify,
)
from ebl.fragmentarium.application.map_site_config import CRS_EPSG, SITE_CONFIGS

ARTIFACT_SUFFIXES = (
    "polygon_inventory.json",
    "findspot_polygon_mappings.json",
    "findspot_polygon_curation_template.json",
    "findspot_polygon_curation_report.md",
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _artifact_names(site_id: str) -> tuple[str, ...]:
    prefix = site_id.lower()
    return tuple(f"{prefix}_{suffix}" for suffix in ARTIFACT_SUFFIXES)


def read_artifact_sets(data_dir: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Map artifact directory does not exist: {data_dir}")
    contents: dict[str, bytes] = {}
    revisions: dict[str, str] = {}
    with artifact_directory_lock(data_dir, exclusive=False):
        for site_id in SITE_CONFIGS:
            manifest_path = data_dir / artifact_manifest_name(site_id.lower())
            if not manifest_path.is_file() or manifest_path.is_symlink():
                raise FileNotFoundError(f"Missing regular artifact: {manifest_path}")
            manifest = load_strict_json(
                manifest_path.read_text(encoding="utf-8"), str(manifest_path)
            )
            if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
                raise ValueError(f"Invalid artifact manifest: {manifest_path}")
            revision = manifest.get("sourceRevision")
            declared_files = manifest.get("files")
            expected_names = set(_artifact_names(site_id))
            if not isinstance(revision, str) or not revision.strip():
                raise ValueError(f"Invalid source revision in {manifest_path}")
            if (
                not isinstance(declared_files, dict)
                or set(declared_files) != expected_names
            ):
                raise ValueError(
                    f"Artifact manifest has unexpected declarations: {manifest_path}"
                )
            revisions[site_id] = revision
            for name in sorted(expected_names):
                expected_hash = declared_files[name]
                path = data_dir / name
                if not isinstance(expected_hash, str):
                    raise ValueError(f"Invalid checksum for {name} in {manifest_path}")
                if not path.is_file() or path.is_symlink():
                    raise FileNotFoundError(f"Missing regular artifact: {path}")
                content = path.read_bytes()
                if _sha256(content) != expected_hash:
                    raise ValueError(f"Artifact checksum mismatch for {name}")
                contents[name] = content
    return contents, revisions


def _json_array(contents: dict[str, bytes], name: str) -> list[object]:
    payload = load_strict_json(contents[name].decode("utf-8"), name)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array in {name}")
    return payload


def _validated_records(
    contents: dict[str, bytes], revisions: dict[str, str], site_id: str
) -> tuple[list[object], list[object], list[object], set[int]]:
    config = SITE_CONFIGS[site_id]
    prefix = site_id.lower()
    inventory = _json_array(contents, f"{prefix}_polygon_inventory.json")
    mappings = _json_array(contents, f"{prefix}_findspot_polygon_mappings.json")
    curation = _json_array(
        contents, f"{prefix}_findspot_polygon_curation_template.json"
    )
    polygon_ids: set[str] = set()
    geometry_checksums: set[str] = set()
    for record in inventory:
        if not isinstance(record, dict) or set(record) != set(
            InventoryRecord.__annotations__
        ):
            raise ValueError(f"Invalid inventory record for {site_id}")
        polygon_id = record.get("polygonId")
        name = record.get("name")
        area_name = record.get("areaName")
        geometry_checksum = record.get("geometryChecksum")
        if (
            not isinstance(polygon_id, str)
            or not isinstance(name, str)
            or not name.strip()
            or contains_control_character(name)
            or not isinstance(area_name, str)
            or not area_name.strip()
            or not isinstance(geometry_checksum, str)
            or re.fullmatch(r"[0-9a-f]{12}", geometry_checksum) is None
            or polygon_id != f"{prefix}-{slugify(name)}-{geometry_checksum}"
            or area_name != polygon_match_key(name)
            or polygon_id in polygon_ids
            or geometry_checksum in geometry_checksums
            or record.get("siteId") != site_id
            or record.get("siteName") != config.site_name
        ):
            raise ValueError(f"Invalid inventory identity for {site_id}")
        polygon_ids.add(polygon_id)
        geometry_checksums.add(geometry_checksum)
    findspot_ids: set[int] = set()
    for kind, records in (("mapping", mappings), ("curation", curation)):
        for record in records:
            expected_type = (
                CuratedMappingRecord if kind == "mapping" else CurationRecord
            )
            if not isinstance(record, dict) or set(record) != set(
                expected_type.__annotations__
            ):
                raise ValueError(f"Invalid {kind} record for {site_id}")
            findspot_id = record.get("findspotId")
            record_polygons = record.get("polygonIds")
            if (
                not isinstance(findspot_id, int)
                or isinstance(findspot_id, bool)
                or not 0 <= findspot_id <= MAX_FINDSPOT_ID
                or findspot_id in findspot_ids
                or not isinstance(record_polygons, list)
                or not all(isinstance(value, str) for value in record_polygons)
                or len(record_polygons) != len(set(record_polygons))
                or not set(record_polygons) <= polygon_ids
            ):
                raise ValueError(f"Invalid {kind} identity for {site_id}")
            if kind == "mapping" and not record_polygons:
                raise ValueError(f"Mapping has no polygons for {site_id}")
            if kind == "mapping":
                MapLocationSchema().load(
                    {
                        key: record.get(key)
                        for key in (
                            "polygonIds",
                            "locationPrecision",
                            "matchMethod",
                            "source",
                            "sourceRevision",
                        )
                    }
                )
            if kind == "curation" and (
                record.get("siteId") != site_id
                or record.get("siteName") != config.site_name
                or record.get("status") != "needs-human-curation"
                or record_polygons
                or record.get("matchMethod") != "curated"
                or record.get("source") != "human curation"
                or record.get("sourceRevision") != revisions[site_id]
                or not isinstance(record.get("requiredDecision"), str)
                or not record["requiredDecision"].strip()
                or record.get("reviewer") != ""
                or record.get("reviewDate") != ""
                or not all(
                    isinstance(record.get(key), str)
                    for key in ("area", "sector", "building", "map")
                )
            ):
                raise ValueError(f"Invalid curation template for {site_id}")
            findspot_ids.add(findspot_id)
    return inventory, mappings, curation, findspot_ids


def site_summary(
    contents: dict[str, bytes], revisions: dict[str, str], site_id: str
) -> tuple[dict[str, object], set[int]]:
    config = SITE_CONFIGS[site_id]
    inventory, mappings, curation, findspot_ids = _validated_records(
        contents, revisions, site_id
    )
    distinct_polygons = {
        polygon_id
        for mapping in mappings
        if isinstance(mapping, dict)
        for polygon_id in mapping["polygonIds"]
    }
    return (
        {
            "siteId": site_id,
            "siteName": config.site_name,
            "authoritativeSource": config.source_label,
            "sourceCrs": CRS_EPSG[config.crs_kind],
            "sourceRevision": revisions[site_id],
            "polygonCount": len(inventory),
            "mappingCount": len(mappings),
            "distinctMappedPolygonCount": len(distinct_polygons),
            "unresolvedCount": len(curation),
        },
        findspot_ids,
    )
