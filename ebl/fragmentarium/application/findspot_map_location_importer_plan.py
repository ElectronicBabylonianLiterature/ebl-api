from __future__ import annotations

from typing import Sequence

from pymongo import UpdateOne

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    ImportIssue,
    MapLocationImportRecord,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema


def build_plan(
    records: Sequence[MapLocationImportRecord],
    findspots: dict[int, object],
    rollback: bool,
    previous_records: Sequence[MapLocationImportRecord] = (),
) -> tuple[tuple[ImportIssue, ...], int, int, int, int, tuple[UpdateOne, ...]]:
    existing = new = changed = skipped = 0
    issues: list[ImportIssue] = []
    operations: list[UpdateOne] = []
    dump_schema = MapLocationSchema()
    previous_by_id = {record.findspot_id: record for record in previous_records}
    for record in records:
        current = getattr(findspots[record.findspot_id], "map_location", None)
        desired = record.map_location
        desired_doc = dump_schema.dump(desired)
        if rollback:
            result = _build_rollback_operation(
                record, current, desired, desired_doc, previous_by_id, dump_schema
            )
            existing += result.existing
            changed += result.changed
            skipped += result.skipped
            operations.extend(result.operations)
            continue
        if current is None:
            if record.findspot_id in previous_by_id:
                issues.append(
                    ImportIssue(
                        record.findspot_id,
                        "expected previous mapLocation is missing",
                    )
                )
                continue
            new += 1
        elif current == desired:
            existing += 1
            continue
        elif record.findspot_id in previous_by_id:
            previous = previous_by_id[record.findspot_id]
            previous_doc = dump_schema.dump(previous.map_location)
            if current != previous.map_location:
                issues.append(
                    ImportIssue(
                        record.findspot_id,
                        "existing mapLocation does not match previous artifact",
                    )
                )
                continue
            changed += 1
            operations.append(
                UpdateOne(
                    {"_id": record.findspot_id, "mapLocation": previous_doc},
                    {"$set": {"mapLocation": desired_doc}},
                )
            )
            continue
        else:
            if previous_records:
                issues.append(
                    ImportIssue(
                        record.findspot_id,
                        "unexpected mapLocation on newly mapped findspot",
                    )
                )
                continue
            changed += 1
        operations.append(
            UpdateOne(
                {"_id": record.findspot_id}, {"$set": {"mapLocation": desired_doc}}
            )
        )
    return tuple(issues), existing, new, changed, skipped, tuple(operations)


def write_operations(collection, operations: Sequence[UpdateOne]) -> int:
    try:
        with collection.database.client.start_session() as session:
            with session.start_transaction():
                return collection.bulk_write(
                    list(operations), ordered=True, session=session
                ).modified_count
    except Exception:
        return collection.bulk_write(list(operations), ordered=True).modified_count


class _RollbackResult:
    def __init__(
        self,
        existing: int = 0,
        changed: int = 0,
        skipped: int = 0,
        operations: Sequence[UpdateOne] = (),
    ) -> None:
        self.existing = existing
        self.changed = changed
        self.skipped = skipped
        self.operations = operations


def _build_rollback_operation(
    record: MapLocationImportRecord,
    current,
    desired,
    desired_doc: dict,
    previous_by_id: dict[int, MapLocationImportRecord],
    dump_schema: MapLocationSchema,
) -> _RollbackResult:
    if previous_by_id:
        previous_record = previous_by_id.get(record.findspot_id)
        previous_doc = (
            dump_schema.dump(previous_record.map_location) if previous_record else None
        )
        if current == desired:
            update = (
                {"$set": {"mapLocation": previous_doc}}
                if previous_doc
                else {"$unset": {"mapLocation": ""}}
            )
            return _RollbackResult(
                changed=1,
                operations=(
                    UpdateOne(
                        {"_id": record.findspot_id, "mapLocation": desired_doc},
                        update,
                    ),
                ),
            )
        if previous_record and current == previous_record.map_location:
            return _RollbackResult(existing=1)
        if current is None and previous_record is None:
            return _RollbackResult(existing=1)
        return _RollbackResult(skipped=1)
    if current is None:
        return _RollbackResult(existing=1)
    if current == desired:
        return _RollbackResult(
            changed=1,
            operations=(
                UpdateOne(
                    {"_id": record.findspot_id, "mapLocation": desired_doc},
                    {"$unset": {"mapLocation": ""}},
                ),
            ),
        )
    return _RollbackResult(skipped=1)
