from __future__ import annotations

import re
from typing import Mapping

from ebl.common.query.parameter_parser import MAX_FINDSPOT_ID
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
from scripts.maps.frontend_transfer_manifest import read_artifact_sets

__all__ = ["read_artifact_sets", "site_summary"]

MAPPING_LOCATION_KEYS = (
    "polygonIds",
    "locationPrecision",
    "matchMethod",
    "source",
    "sourceRevision",
)
CURATION_TEMPLATE_VALUES = {
    "status": "needs-human-curation",
    "polygonIds": [],
    "matchMethod": "curated",
    "source": "human curation",
    "reviewer": "",
    "reviewDate": "",
}
CURATION_TEXT_KEYS = ("area", "sector", "building", "map")
INVENTORY_KEYS = frozenset(InventoryRecord.__annotations__)
RECORD_KEYS = {
    "mapping": frozenset(CuratedMappingRecord.__annotations__),
    "curation": frozenset(CurationRecord.__annotations__),
}


def _json_array(contents: dict[str, bytes], name: str) -> list[object]:
    payload = load_strict_json(contents[name].decode("utf-8"), name)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array in {name}")
    return payload


def _typed_record(record: object, keys: frozenset[str], error: str) -> dict:
    if not isinstance(record, dict) or set(record) != keys:
        raise ValueError(error)
    return record


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _differs(record: dict, expected: Mapping[str, object]) -> bool:
    return any(record.get(key) != value for key, value in expected.items())


def _inventory_identity(record: dict, site_id: str) -> tuple[str, str]:
    error = f"Invalid inventory identity for {site_id}"
    name = record.get("name")
    checksum = record.get("geometryChecksum")
    if (
        not isinstance(name, str)
        or not name.strip()
        or contains_control_character(name)
    ):
        raise ValueError(error)
    if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{12}", checksum):
        raise ValueError(error)
    polygon_id = f"{site_id.lower()}-{slugify(name)}-{checksum}"
    expected = {
        "polygonId": polygon_id,
        "areaName": polygon_match_key(name),
        "siteId": site_id,
        "siteName": SITE_CONFIGS[site_id].site_name,
    }
    if not _is_text(record.get("areaName")) or _differs(record, expected):
        raise ValueError(error)
    return polygon_id, checksum


def _validated_polygon_ids(inventory: list[object], site_id: str) -> set[str]:
    polygon_ids: set[str] = set()
    checksums: set[str] = set()
    for item in inventory:
        record = _typed_record(
            item, INVENTORY_KEYS, f"Invalid inventory record for {site_id}"
        )
        polygon_id, checksum = _inventory_identity(record, site_id)
        if polygon_id in polygon_ids or checksum in checksums:
            raise ValueError(f"Invalid inventory identity for {site_id}")
        polygon_ids.add(polygon_id)
        checksums.add(checksum)
    return polygon_ids


def _is_polygon_id_list(value: object, polygon_ids: set[str]) -> bool:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return False
    return len(value) == len(set(value)) and set(value) <= polygon_ids


def _findspot_identity(
    record: dict, kind: str, site_id: str, polygon_ids: set[str]
) -> int:
    findspot_id = record.get("findspotId")
    if (
        not isinstance(findspot_id, int)
        or isinstance(findspot_id, bool)
        or not _is_polygon_id_list(record.get("polygonIds"), polygon_ids)
    ):
        raise ValueError(f"Invalid {kind} identity for {site_id}")
    if not 0 <= findspot_id <= MAX_FINDSPOT_ID:
        raise ValueError(f"Invalid {kind} identity for {site_id}")
    return findspot_id


def _validate_mapping(record: dict, site_id: str) -> None:
    if not record["polygonIds"]:
        raise ValueError(f"Mapping has no polygons for {site_id}")
    MapLocationSchema().load({key: record.get(key) for key in MAPPING_LOCATION_KEYS})


def _validate_curation(record: dict, site_id: str, revision: str) -> None:
    expected = {
        **CURATION_TEMPLATE_VALUES,
        "siteId": site_id,
        "siteName": SITE_CONFIGS[site_id].site_name,
        "sourceRevision": revision,
    }
    if (
        _differs(record, expected)
        or not _is_text(record.get("requiredDecision"))
        or not all(isinstance(record.get(key), str) for key in CURATION_TEXT_KEYS)
    ):
        raise ValueError(f"Invalid curation template for {site_id}")


def _validated_findspot_ids(
    records_by_kind: dict[str, list[object]],
    site_id: str,
    revision: str,
    polygon_ids: set[str],
) -> set[int]:
    findspot_ids: set[int] = set()
    for kind, records in records_by_kind.items():
        for item in records:
            error = f"Invalid {kind} record for {site_id}"
            record = _typed_record(item, RECORD_KEYS[kind], error)
            findspot_id = _findspot_identity(record, kind, site_id, polygon_ids)
            if findspot_id in findspot_ids:
                raise ValueError(f"Invalid {kind} identity for {site_id}")
            if kind == "mapping":
                _validate_mapping(record, site_id)
            else:
                _validate_curation(record, site_id, revision)
            findspot_ids.add(findspot_id)
    return findspot_ids


def site_summary(
    contents: dict[str, bytes], revisions: dict[str, str], site_id: str
) -> tuple[dict[str, object], set[int]]:
    config = SITE_CONFIGS[site_id]
    prefix = site_id.lower()
    inventory = _json_array(contents, f"{prefix}_polygon_inventory.json")
    mappings = _json_array(contents, f"{prefix}_findspot_polygon_mappings.json")
    curation = _json_array(
        contents, f"{prefix}_findspot_polygon_curation_template.json"
    )
    polygon_ids = _validated_polygon_ids(inventory, site_id)
    findspot_ids = _validated_findspot_ids(
        {"mapping": mappings, "curation": curation},
        site_id,
        revisions[site_id],
        polygon_ids,
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
