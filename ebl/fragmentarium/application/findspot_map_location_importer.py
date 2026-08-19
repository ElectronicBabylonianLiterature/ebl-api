from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from marshmallow import ValidationError

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    ASSUR_SITE_ID,
    DEFAULT_INVENTORY_PATH,
    DEFAULT_MAPPINGS_PATH,
    ImportIssue,
    ImportSummary,
    MapLocationImportRecord,
    MapLocationImportRecordSchema,
)
from ebl.fragmentarium.application.findspot_map_location_importer_plan import (
    build_plan,
    write_operations,
)
from ebl.fragmentarium.application.findspot_map_location_target import (
    DEVELOPMENT_CLASSIFICATION,
    MappingInputs,
    fingerprint_database,
)
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.provenance.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.transliteration.infrastructure.collections import FINDSPOTS_COLLECTION


def load_polygon_inventory(path: Path | str) -> set[str]:
    data = _load_json_array(path)
    polygon_ids = set()
    for index, entry in enumerate(data):
        if not isinstance(entry, dict) or "polygonId" not in entry:
            raise ValueError(f"Inventory entry {index} is missing polygonId.")
        polygon_id = entry["polygonId"]
        if not isinstance(polygon_id, str) or not polygon_id.strip():
            raise ValueError(f"Inventory entry {index} has an invalid polygonId.")
        polygon_ids.add(polygon_id)
    return polygon_ids


def load_import_records(
    path: Path | str, polygon_ids: set[str]
) -> tuple[tuple[MapLocationImportRecord, ...], tuple[ImportIssue, ...], int]:
    data = _load_json_array(path)
    schema = MapLocationImportRecordSchema()
    records = []
    issues: list[ImportIssue] = []
    seen_findspot_ids: set[int] = set()
    for entry in data:
        try:
            record = schema.load(entry)
        except (ValidationError, ValueError, TypeError) as error:
            issues.append(
                ImportIssue(_findspot_id(entry), f"validation failed: {error}")
            )
            continue
        if record.findspot_id in seen_findspot_ids:
            issues.append(ImportIssue(record.findspot_id, "duplicate mapping record"))
            continue
        missing_ids = [
            pid for pid in record.map_location.polygon_ids if pid not in polygon_ids
        ]
        if missing_ids:
            issues.append(
                ImportIssue(
                    record.findspot_id,
                    f"polygonIds not found in inventory: {missing_ids}",
                )
            )
            continue
        seen_findspot_ids.add(record.findspot_id)
        records.append(record)
    return tuple(records), tuple(issues), len(data)


@dataclass(frozen=True)
class ImportPaths:
    mappings: Path | str = DEFAULT_MAPPINGS_PATH
    inventory: Path | str = DEFAULT_INVENTORY_PATH
    previous_mappings: Path | str | None = None
    previous_inventory: Path | str | None = None


def run_import(
    database,
    paths: ImportPaths | None = None,
    dry_run: bool = True,
    rollback: bool = False,
) -> ImportSummary:
    paths = paths or ImportPaths()
    polygon_ids = load_polygon_inventory(paths.inventory)
    records, issues, scanned = load_import_records(paths.mappings, polygon_ids)
    previous_records = _load_previous_records(
        paths.previous_mappings, paths.previous_inventory
    )
    findspots = _load_findspots(database)
    valid_records, site_issues = _validate_findspots(records, findspots)
    issues = issues + site_issues
    plan_issues, existing, new, changed, skipped, operations = build_plan(
        valid_records, findspots, rollback, previous_records
    )
    issues = issues + plan_issues
    issue_counts = _count_issues(issues)
    fingerprint = fingerprint_database(
        database, MappingInputs(valid_records, polygon_ids, previous_records)
    )

    applied = 0
    if not dry_run and not issues and operations:
        applied = write_operations(database[FINDSPOTS_COLLECTION], operations)

    return ImportSummary(
        scanned=scanned,
        valid=len(valid_records),
        invalid=len(issues),
        unknown_findspots=issue_counts["unknown_findspots"],
        wrong_site=issue_counts["wrong_site"],
        unknown_polygons=issue_counts["unknown_polygons"],
        existing=existing,
        new=new,
        changed=changed,
        skipped=skipped,
        applied=applied,
        dry_run=dry_run,
        rollback=rollback,
        issues=issues,
        database_classification=DEVELOPMENT_CLASSIFICATION
        if fingerprint.is_approved_development
        else "local",
        total_findspots=fingerprint.total_findspots,
        assur_findspots=fingerprint.assur_findspots,
        unresolved_assur_findspots=fingerprint.unresolved_assur_findspots,
    )


def _load_previous_records(
    previous_mappings_path: Path | str | None,
    previous_inventory_path: Path | str | None,
) -> tuple[MapLocationImportRecord, ...]:
    if previous_mappings_path is None:
        return ()
    if previous_inventory_path is None:
        raise ValueError("previous inventory is required with previous mappings")
    previous_polygon_ids = load_polygon_inventory(previous_inventory_path)
    records, issues, _ = load_import_records(
        previous_mappings_path, previous_polygon_ids
    )
    if issues:
        raise ValueError("previous mappings are invalid")
    return records


def _count_issues(issues: Sequence[ImportIssue]) -> dict[str, int]:
    return {
        "unknown_findspots": sum(
            issue.reason == "findspot not found" for issue in issues
        ),
        "wrong_site": sum(issue.reason == "findspot is not Aššur" for issue in issues),
        "unknown_polygons": sum(
            issue.reason.startswith("polygonIds not found in inventory")
            for issue in issues
        ),
    }


def _load_findspots(database) -> dict[int, object]:
    provenance_service = ProvenanceService(MongoProvenanceRepository(database))
    repository = MongoFindspotRepository(database, provenance_service)
    return {findspot.id_: findspot for findspot in repository.find_all()}


def _validate_findspots(
    records: Sequence[MapLocationImportRecord], findspots: dict[int, object]
) -> tuple[tuple[MapLocationImportRecord, ...], tuple[ImportIssue, ...]]:
    valid_records = []
    issues: list[ImportIssue] = []
    for record in records:
        findspot = findspots.get(record.findspot_id)
        if findspot is None:
            issues.append(ImportIssue(record.findspot_id, "findspot not found"))
            continue
        site = getattr(findspot, "site", None)
        if site is None or getattr(site, "id", None) != ASSUR_SITE_ID:
            issues.append(ImportIssue(record.findspot_id, "findspot is not Aššur"))
            continue
        valid_records.append(record)
    return tuple(valid_records), tuple(issues)


def _load_json_array(path: Path | str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}.")
    return data


def _findspot_id(entry) -> int | None:
    if isinstance(entry, dict):
        value = entry.get("findspotId")
        return value if isinstance(value, int) else None
    return None
