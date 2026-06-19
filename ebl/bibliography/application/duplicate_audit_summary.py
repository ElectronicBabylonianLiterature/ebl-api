from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping, Optional, Sequence

from ebl.bibliography.application.duplicate_audit_candidates import group_by_exact
from ebl.bibliography.application.duplicate_audit_normalization import (
    NormalizedBibliographyEntry,
)
from ebl.bibliography.application.duplicate_audit_scoring import PairScore
from ebl.bibliography.application.duplicate_audit_usage import UsageCounts


def metadata_completeness(entry: NormalizedBibliographyEntry) -> float:
    fields = (
        entry.title,
        entry.contributors,
        entry.year,
        entry.doi or entry.isbn,
        entry.container_title or entry.publisher,
        entry.volume or entry.edition,
        entry.page or entry.issue,
        entry.type,
    )
    return round(sum(1 for value in fields if value) / len(fields), 4)


def suggest_canonical(
    entries: Sequence[NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts] | None = None,
) -> tuple[str, str]:
    usage_counts_by_id = usage_counts or {}
    winner = max(entries, key=lambda entry: canonical_score(entry, usage_counts_by_id))
    usage = usage_counts_by_id.get(winner.id, UsageCounts()).total
    return (
        winner.id,
        f"Highest metadata completeness ({metadata_completeness(winner)}), "
        f"identifier strength ({identifier_strength(winner)}), "
        f"and usage count ({usage}).",
    )


def canonical_score(
    entry: NormalizedBibliographyEntry, usage_counts: Mapping[str, UsageCounts]
) -> tuple[float, int, str]:
    usage = usage_counts.get(entry.id, UsageCounts()).total
    return (
        metadata_completeness(entry)
        + identifier_bonus(entry)
        + min(usage, 50) / 500
        + stable_id_bonus(entry.id),
        usage,
        entry.id,
    )


def identifier_bonus(entry: NormalizedBibliographyEntry) -> float:
    if entry.doi:
        return 0.15
    if entry.isbn:
        return 0.08
    return 0.0


def identifier_strength(entry: NormalizedBibliographyEntry) -> str:
    if entry.doi:
        return "DOI"
    if entry.isbn:
        return "ISBN"
    return "none"


def stable_id_bonus(id_: str) -> float:
    return 0.02 if re.match(r"^[A-Za-z0-9_.:-]+$", id_) else 0.0


def summarize_signals(
    signals: Iterable[Mapping[str, Optional[float]]],
) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for signal in signals:
        for key, value in signal.items():
            if value is not None:
                values[key].append(value)
    return {
        key: round(sum(field_values) / len(field_values), 4)
        for key, field_values in sorted(values.items())
    }


def member_summary(
    entry: NormalizedBibliographyEntry, usage: UsageCounts
) -> dict[str, Any]:
    return {
        "id": entry.id,
        "title": entry.raw.get("title"),
        "authorEditorSummary": author_editor_summary(entry.raw),
        "year": entry.year,
        "DOI": entry.raw.get("DOI"),
        "ISBN": entry.raw.get("ISBN"),
        "ISSN": entry.raw.get("ISSN"),
        "type": entry.type,
        "containerTitle": entry.raw.get("container-title"),
        "volume": entry.raw.get("volume"),
        "issue": entry.raw.get("issue"),
        "page": entry.raw.get("page"),
        "usageCounts": usage.to_dict(),
        "metadataCompletenessScore": metadata_completeness(entry),
    }


def author_editor_summary(entry: Mapping[str, Any]) -> str:
    people = entry.get("author") or entry.get("editor") or ()
    names = []
    for person in people[:3]:
        if person.get("literal"):
            names.append(person["literal"])
        else:
            names.append(
                " ".join(
                    part for part in (person.get("given"), person.get("family")) if part
                )
            )
    return "; ".join(names)


def pair_to_dict(pair: PairScore) -> dict[str, Any]:
    return {
        "leftId": pair.left_id,
        "rightId": pair.right_id,
        "score": pair.score,
        "decision": pair.decision,
        "matchedSignals": pair.matched_signals,
        "conflictingSignals": pair.conflicting_signals,
        "evidenceCompleteness": pair.evidence_completeness,
        "reason": pair.reason,
        "recommendation": pair.recommendation,
        "previouslyReviewedNotDuplicate": pair.previously_reviewed_not_duplicate,
    }


def audit_statistics(
    entries: Sequence[NormalizedBibliographyEntry], pairs: Sequence[PairScore]
) -> dict[str, Any]:
    return {
        "totalRecordsScanned": len(entries),
        "missingTitle": count_missing(entries, "title"),
        "missingAuthorEditor": sum(1 for entry in entries if not entry.contributors),
        "missingYear": sum(1 for entry in entries if entry.year is None),
        "withDOI": count_present(entries, "doi"),
        "withISBN": count_present(entries, "isbn"),
        "withISSN": count_present(entries, "issn"),
        "exactDOIDuplicateGroups": len(group_by_exact(entries, "doi")),
        "exactISBNDuplicateGroups": len(group_by_exact(entries, "isbn")),
        "exactISSNSupportGroups": len(group_by_exact(entries, "issn")),
        "scoreDistribution": score_distribution(pairs),
    }


def count_missing(entries: Sequence[NormalizedBibliographyEntry], field: str) -> int:
    return sum(1 for entry in entries if not getattr(entry, field))


def count_present(entries: Sequence[NormalizedBibliographyEntry], field: str) -> int:
    return sum(1 for entry in entries if getattr(entry, field))


def score_distribution(pairs: Sequence[PairScore]) -> dict[str, int]:
    score_buckets = Counter()
    for pair in pairs:
        bucket_start = int(pair.score * 10) / 10
        score_buckets[f"{bucket_start:.1f}-{bucket_start + 0.1:.1f}"] += 1
    return dict(sorted(score_buckets.items()))
