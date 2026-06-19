from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ebl.bibliography.application.duplicate_audit_candidates import (
    generate_candidate_pairs,
    reviewed_not_duplicate_pairs,
)
from ebl.bibliography.application.duplicate_audit_groups import (
    CandidateGroup,
    cluster_pairs,
)
from ebl.bibliography.application.duplicate_audit_normalization import (
    PROJECTION,
    normalize_entry,
)
from ebl.bibliography.application.duplicate_audit_reports import write_reports
from ebl.bibliography.application.duplicate_audit_scoring import PairScore
from ebl.bibliography.application.duplicate_audit_usage import collect_usage_counts


def run_audit(
    database: Any,
    output_dir: Path,
    overrides_path: Optional[Path] = None,
) -> tuple[list[PairScore], list[CandidateGroup]]:
    entries = [
        normalize_entry(entry)
        for entry in database["bibliography"].find({}, projection=PROJECTION)
    ]
    false_positive_pairs = reviewed_not_duplicate_pairs(overrides_path)
    pairs = generate_candidate_pairs(entries, false_positive_pairs)
    ids_in_groups = {
        id_
        for pair in pairs
        if pair.decision
        in {"likely_duplicate", "possible_duplicate", "insufficient_data"}
        for id_ in (pair.left_id, pair.right_id)
    }
    usage_counts = collect_usage_counts(database, ids_in_groups)
    groups = cluster_pairs(pairs, {entry.id: entry for entry in entries}, usage_counts)
    write_reports(output_dir, entries, pairs, groups)
    return pairs, groups
