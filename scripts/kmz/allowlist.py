from __future__ import annotations

import json
from dataclasses import replace
from itertools import chain
from pathlib import Path
from typing import Mapping

from scripts.kmz.models import ImportPlan, ProposedUpdate, SkippedRecord


def filter_plan_by_allowlist(
    plan: ImportPlan, allowlist: Mapping[str, set[str] | None] | None
) -> ImportPlan:
    if allowlist is None:
        return plan

    exact_updates = tuple(
        update
        for update in plan.proposed_updates
        if _allowlist_allows(allowlist, update)
    )
    approved_normalized_updates = tuple(
        replace(
            update,
            reason_safe="Normalized unique match explicitly approved by field allowlist",
        )
        for update in plan.review_candidates
        if allowlist.get(update.provenance_id) is not None
        and _allowlist_allows(allowlist, update)
    )
    review_candidates = tuple(
        update
        for update in plan.review_candidates
        if allowlist.get(update.provenance_id) is None
        and _allowlist_allows(allowlist, update)
    )
    skipped_records = [
        *plan.skipped_records,
        *(
            SkippedRecord(
                update.provenance_id,
                update.long_name,
                "not in allowlist",
                update.placemark_name,
            )
            for update in chain(plan.proposed_updates, plan.review_candidates)
            if not _allowlist_allows(allowlist, update)
        ),
    ]
    return replace(
        plan,
        proposed_updates=tuple(chain(exact_updates, approved_normalized_updates)),
        review_candidates=review_candidates,
        skipped_records=tuple(skipped_records),
    )


def load_allowlist(path: Path | str | None) -> Mapping[str, set[str] | None] | None:
    if path is None:
        return None

    data = json.loads(Path(path).read_text())
    entries = data.get("updates", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError(
            "Allowlist must be a JSON list or an object with an updates list"
        )

    allowlist: dict[str, set[str] | None] = {}
    for entry in entries:
        if isinstance(entry, str):
            allowlist[entry] = None
            continue
        if not isinstance(entry, dict):
            raise ValueError("Allowlist entries must be strings or objects")
        provenance_id = entry.get("id") or entry.get("_id")
        if not isinstance(provenance_id, str):
            raise ValueError("Allowlist object entries require an id")
        fields = entry.get("fields")
        allowlist[provenance_id] = set(fields) if fields else None
    return allowlist


def _allowlist_allows(
    allowlist: Mapping[str, set[str] | None] | None, proposed_update: ProposedUpdate
) -> bool:
    if allowlist is None:
        return True
    allowed_fields = allowlist.get(proposed_update.provenance_id)
    if proposed_update.provenance_id not in allowlist:
        return False
    return allowed_fields is None or set(proposed_update.fields) <= allowed_fields
