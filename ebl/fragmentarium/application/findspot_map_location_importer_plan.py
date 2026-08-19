from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from pymongo import UpdateOne

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    ImportIssue,
    MapLocationImportRecord,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema


@dataclass(frozen=True)
class _RecordContext:
    record: MapLocationImportRecord
    current: object
    desired_doc: dict


@dataclass(frozen=True)
class _PlanContext:
    previous_by_id: dict[int, MapLocationImportRecord]
    dump_schema: MapLocationSchema
    has_previous_records: bool


class _PlanStepResult:
    def __init__(
        self,
        existing: int = 0,
        new: int = 0,
        changed: int = 0,
        skipped: int = 0,
        issue: ImportIssue | None = None,
        operations: Sequence[UpdateOne] = (),
    ) -> None:
        self.existing = existing
        self.new = new
        self.changed = changed
        self.skipped = skipped
        self.issue = issue
        self.operations = operations


def build_plan(
    records: Sequence[MapLocationImportRecord],
    findspots: dict[int, object],
    rollback: bool,
    previous_records: Sequence[MapLocationImportRecord] = (),
) -> tuple[tuple[ImportIssue, ...], int, int, int, int, tuple[UpdateOne, ...]]:
    existing = new = changed = skipped = 0
    issues: list[ImportIssue] = []
    operations: list[UpdateOne] = []
    plan = _PlanContext(
        previous_by_id={record.findspot_id: record for record in previous_records},
        dump_schema=MapLocationSchema(),
        has_previous_records=bool(previous_records),
    )
    build_step = _build_rollback_operation if rollback else _build_forward_operation
    for record in records:
        context = _RecordContext(
            record=record,
            current=getattr(findspots[record.findspot_id], "map_location", None),
            desired_doc=plan.dump_schema.dump(record.map_location),
        )
        result = build_step(context, plan)
        existing += result.existing
        new += result.new
        changed += result.changed
        skipped += result.skipped
        if result.issue is not None:
            issues.append(result.issue)
        operations.extend(result.operations)
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


def _set_map_location_operation(
    findspot_id: int, desired_doc: dict
) -> tuple[UpdateOne]:
    return (UpdateOne({"_id": findspot_id}, {"$set": {"mapLocation": desired_doc}}),)


def _build_forward_operation(
    context: _RecordContext, plan: _PlanContext
) -> _PlanStepResult:
    record, current, desired_doc = context.record, context.current, context.desired_doc
    previous_record = plan.previous_by_id.get(record.findspot_id)

    if current is None:
        if previous_record is not None:
            return _PlanStepResult(
                issue=ImportIssue(
                    record.findspot_id, "expected previous mapLocation is missing"
                )
            )
        return _PlanStepResult(
            new=1,
            operations=_set_map_location_operation(record.findspot_id, desired_doc),
        )

    if current == record.map_location:
        return _PlanStepResult(existing=1)

    if previous_record is not None:
        if current != previous_record.map_location:
            return _PlanStepResult(
                issue=ImportIssue(
                    record.findspot_id,
                    "existing mapLocation does not match previous artifact",
                )
            )
        previous_doc = plan.dump_schema.dump(previous_record.map_location)
        return _PlanStepResult(
            changed=1,
            operations=(
                UpdateOne(
                    {"_id": record.findspot_id, "mapLocation": previous_doc},
                    {"$set": {"mapLocation": desired_doc}},
                ),
            ),
        )

    if plan.has_previous_records:
        return _PlanStepResult(
            issue=ImportIssue(
                record.findspot_id, "unexpected mapLocation on newly mapped findspot"
            )
        )
    return _PlanStepResult(
        changed=1,
        operations=_set_map_location_operation(record.findspot_id, desired_doc),
    )


def _build_rollback_operation(
    context: _RecordContext, plan: _PlanContext
) -> _PlanStepResult:
    if plan.previous_by_id:
        return _build_rollback_with_previous(context, plan)
    return _build_rollback_without_previous(context)


def _build_rollback_with_previous(
    context: _RecordContext, plan: _PlanContext
) -> _PlanStepResult:
    record, current, desired_doc = context.record, context.current, context.desired_doc
    previous_record = plan.previous_by_id.get(record.findspot_id)

    if current == record.map_location:
        previous_doc = (
            plan.dump_schema.dump(previous_record.map_location)
            if previous_record
            else None
        )
        update = (
            {"$set": {"mapLocation": previous_doc}}
            if previous_doc
            else {"$unset": {"mapLocation": ""}}
        )
        return _PlanStepResult(
            changed=1,
            operations=(
                UpdateOne(
                    {"_id": record.findspot_id, "mapLocation": desired_doc}, update
                ),
            ),
        )
    if current is None and previous_record is None:
        return _PlanStepResult(existing=1)
    if previous_record and current == previous_record.map_location:
        return _PlanStepResult(existing=1)
    return _PlanStepResult(skipped=1)


def _build_rollback_without_previous(context: _RecordContext) -> _PlanStepResult:
    record, current, desired_doc = context.record, context.current, context.desired_doc

    if current is None:
        return _PlanStepResult(existing=1)
    if current == record.map_location:
        return _PlanStepResult(
            changed=1,
            operations=(
                UpdateOne(
                    {"_id": record.findspot_id, "mapLocation": desired_doc},
                    {"$unset": {"mapLocation": ""}},
                ),
            ),
        )
    return _PlanStepResult(skipped=1)
