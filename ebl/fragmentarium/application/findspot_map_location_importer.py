from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from marshmallow import ValidationError
from pymongo import UpdateOne

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    ASSUR_SITE_ID,
    DEFAULT_INVENTORY_PATH,
    DEFAULT_MAPPINGS_PATH,
    ImportIssue,
    ImportSummary,
    MapLocationImportRecord,
    MapLocationImportRecordSchema,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
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


def run_import(
    database,
    mappings_path: Path | str = DEFAULT_MAPPINGS_PATH,
    inventory_path: Path | str = DEFAULT_INVENTORY_PATH,
    dry_run: bool = True,
    rollback: bool = False,
) -> ImportSummary:
    polygon_ids = load_polygon_inventory(inventory_path)
    records, issues, scanned = load_import_records(mappings_path, polygon_ids)
    findspots = _load_findspots(database)
    valid_records, site_issues = _validate_findspots(records, findspots)
    issues = (*issues, *site_issues)
    existing, new, changed, skipped, operations = _build_plan(
        valid_records, findspots, rollback
    )

    applied = 0
    if not dry_run and not issues and operations:
        applied = _write_operations(database[FINDSPOTS_COLLECTION], operations)

    return ImportSummary(
        scanned=scanned,
        valid=len(valid_records),
        invalid=len(issues),
        existing=existing,
        new=new,
        changed=changed,
        skipped=skipped,
        applied=applied,
        dry_run=dry_run,
        rollback=rollback,
        issues=issues,
    )


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


def _build_plan(
    records: Sequence[MapLocationImportRecord],
    findspots: dict[int, object],
    rollback: bool,
) -> tuple[int, int, int, int, tuple[UpdateOne, ...]]:
    existing = new = changed = skipped = 0
    operations: list[UpdateOne] = []
    dump_schema = MapLocationSchema()
    for record in records:
        current = getattr(findspots[record.findspot_id], "map_location", None)
        desired = record.map_location
        desired_doc = dump_schema.dump(desired)
        if rollback:
            if current is None:
                existing += 1
                continue
            if current == desired:
                changed += 1
                operations.append(
                    UpdateOne(
                        {"_id": record.findspot_id, "mapLocation": desired_doc},
                        {"$unset": {"mapLocation": ""}},
                    )
                )
            else:
                skipped += 1
            continue
        if current is None:
            new += 1
        elif current == desired:
            existing += 1
            continue
        else:
            changed += 1
        operations.append(
            UpdateOne(
                {"_id": record.findspot_id}, {"$set": {"mapLocation": desired_doc}}
            )
        )
    return existing, new, changed, skipped, tuple(operations)


def _write_operations(collection, operations: Sequence[UpdateOne]) -> int:
    try:
        with collection.database.client.start_session() as session:
            with session.start_transaction():
                return collection.bulk_write(
                    list(operations), ordered=True, session=session
                ).modified_count
    except Exception:
        return collection.bulk_write(list(operations), ordered=True).modified_count


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
