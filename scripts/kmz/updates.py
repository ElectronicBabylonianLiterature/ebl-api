from __future__ import annotations

from typing import Any, Mapping, Sequence

from scripts.kmz.allowlist import _allowlist_allows
from scripts.kmz.models import ProposedUpdate


def apply_proposed_updates(
    collection: Any,
    proposed_updates: Sequence[ProposedUpdate],
    allowlist: Mapping[str, set[str] | None] | None = None,
) -> tuple[dict[str, Any], ...]:
    applied_updates: list[dict[str, Any]] = []
    for proposed_update in proposed_updates:
        if not _allowlist_allows(allowlist, proposed_update):
            applied_updates.append(
                {
                    "id": proposed_update.provenance_id,
                    "fields": list(proposed_update.fields),
                    "matchedCount": 0,
                    "modifiedCount": 0,
                    "skippedReason": "not in allowlist",
                }
            )
            continue

        update_filter = build_no_overwrite_filter(
            proposed_update.provenance_id, proposed_update.fields
        )
        update = {"$set": _build_set_update(proposed_update)}
        result = collection.update_one(update_filter, update)
        applied_updates.append(
            {
                "id": proposed_update.provenance_id,
                "fields": list(proposed_update.fields),
                "matchedCount": result.matched_count,
                "modifiedCount": result.modified_count,
            }
        )
    return tuple(applied_updates)


def build_no_overwrite_filter(
    provenance_id: str, fields: Sequence[str]
) -> dict[str, Any]:
    missing_checks = [_missing_field_filter(field) for field in fields]
    if len(missing_checks) == 1:
        return {"_id": provenance_id, **missing_checks[0]}
    return {"_id": provenance_id, "$and": missing_checks}


def _build_set_update(proposed_update: ProposedUpdate) -> dict[str, Any]:
    update: dict[str, Any] = {}
    if "coordinates" in proposed_update.fields:
        update["coordinates"] = proposed_update.coordinate
    if "polygonCoordinates" in proposed_update.fields:
        update["polygonCoordinates"] = list(proposed_update.polygon_coordinates)
    return update


def _missing_field_filter(field: str) -> dict[str, Any]:
    return {"$or": [{field: {"$exists": False}}, {field: None}]}
