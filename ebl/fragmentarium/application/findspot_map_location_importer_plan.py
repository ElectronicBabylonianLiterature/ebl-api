from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from pymongo import UpdateOne
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

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


@dataclass(frozen=True)
class _PlanStepResult:
    existing: int = 0
    new: int = 0
    changed: int = 0
    skipped: int = 0
    issue: ImportIssue | None = None
    operations: Sequence[UpdateOne] = ()


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
        desired_doc = plan.dump_schema.dump(record.map_location)
        assert isinstance(desired_doc, dict)
        context = _RecordContext(
            record=record,
            current=getattr(findspots[record.findspot_id], "map_location", None),
            desired_doc=desired_doc,
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


class _StandaloneTransactionUnsupported(Exception):
    pass


def write_operations(collection: Collection, operations: Sequence[UpdateOne]) -> int:
    try:
        with collection.database.client.start_session() as session:
            with session.start_transaction():
                return _write_transaction_batch(collection, operations, session)
    except _StandaloneTransactionUnsupported:
        return collection.bulk_write(list(operations), ordered=True).modified_count


def _write_transaction_batch(
    collection: Collection, operations: Sequence[UpdateOne], session: ClientSession
) -> int:
    try:
        return collection.bulk_write(
            list(operations), ordered=True, session=session
        ).modified_count
    except OperationFailure as error:
        unsupported_message = (
            "Transaction numbers are only allowed on a replica set member or mongos"
        )
        if error.code != 20 or unsupported_message not in str(error):
            raise
        raise _StandaloneTransactionUnsupported from error


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

    return _build_replacement_operation(context, plan)


def _build_replacement_operation(
    context: _RecordContext, plan: _PlanContext
) -> _PlanStepResult:
    record, current, desired_doc = context.record, context.current, context.desired_doc
    previous_record = plan.previous_by_id.get(record.findspot_id)
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
