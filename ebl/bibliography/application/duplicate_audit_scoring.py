from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from ebl.bibliography.application.duplicate_audit_conflicts import (
    calibrated_conflicting_signals,
)
from ebl.bibliography.application.duplicate_audit_normalization import (
    NormalizedBibliographyEntry,
)
from ebl.bibliography.application.duplicate_audit_similarity import (
    matched_signals,
    pair_type,
    type_weights,
)


@dataclass
class PairScore:
    left_id: str
    right_id: str
    score: float
    decision: str
    matched_signals: dict[str, Optional[float]]
    conflicting_signals: list[str]
    evidence_completeness: float
    reason: str
    recommendation: str
    previously_reviewed_not_duplicate: bool = False


def usable_signal_weight(
    matched: Mapping[str, Optional[float]], weights: Mapping[str, float]
) -> float:
    return float(
        sum(
            weight
            for signal, weight in weights.items()
            if matched.get(signal) is not None
        )
    )


def signal_evidence_completeness(
    matched: Mapping[str, Optional[float]], weights: Mapping[str, float]
) -> float:
    total_weight = float(sum(weights.values()))
    return round(usable_signal_weight(matched, weights) / total_weight, 4)


def weighted_match_score(
    matched: Mapping[str, Optional[float]], weights: Mapping[str, float]
) -> float:
    usable_weight = usable_signal_weight(matched, weights)
    if not usable_weight:
        return 0.0
    return (
        sum((matched.get(signal) or 0.0) * weight for signal, weight in weights.items())
        / usable_weight
    )


def adjust_identifier_score(
    score: float, matched: Mapping[str, Optional[float]], conflicts: Sequence[str]
) -> float:
    if matched["doi"] == 1.0:
        score = max(score, 0.86 if conflicts else 0.97)
    if matched["isbn"] == 1.0 and (matched.get("title") or 0.0) >= 0.7:
        score = max(score, 0.94)
    if matched["issn"] == 1.0 and score < 0.76:
        score = min(score + 0.06, 0.75)
    return score


def pair_decision(
    score: float,
    evidence_completeness: float,
    previously_reviewed_not_duplicate: bool,
    conflicts: Sequence[str],
    matched: Mapping[str, Optional[float]],
) -> tuple[str, str]:
    exact_identifier_match = has_exact_identifier_match(matched)
    rules = (
        (
            previously_reviewed_not_duplicate,
            "not_duplicate",
            "ignore_previously_reviewed",
        ),
        (
            evidence_completeness < 0.35,
            "insufficient_data",
            "manual_review_if_important",
        ),
        (
            "different_entry_title" in conflicts
            or "different_webpage_title" in conflicts,
            "not_duplicate",
            "allow_create",
        ),
        (
            "series_part" in conflicts and exact_identifier_match,
            "possible_duplicate",
            "review_series_sibling",
        ),
        ("series_part" in conflicts, "not_duplicate", "allow_create"),
        (
            "doi_data_issue" in conflicts,
            "possible_duplicate",
            "review_identifier_conflict",
        ),
        (
            "different_title" in conflicts and not exact_identifier_match,
            "not_duplicate",
            "allow_create",
        ),
        (
            has_conservative_conflict(conflicts) and score >= 0.76,
            "possible_duplicate",
            "review_conflicting_metadata",
        ),
        (score >= 0.92, "likely_duplicate", "confirm_before_cleanup"),
        (score >= 0.76, "possible_duplicate", "review_before_create_or_cleanup"),
    )
    return next(
        (
            (decision, recommendation)
            for applies, decision, recommendation in rules
            if applies
        ),
        ("not_duplicate", "allow_create"),
    )


def has_exact_identifier_match(matched: Mapping[str, Optional[float]]) -> bool:
    return matched.get("doi") == 1.0 or matched.get("isbn") == 1.0


def has_conservative_conflict(conflicts: Sequence[str]) -> bool:
    conflict_set = set(conflicts)
    return bool(
        {
            "different_page",
            "different_volume",
            "different_issue",
        }.intersection(conflict_set)
    )


def score_pair(
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
    *,
    previously_reviewed_not_duplicate: bool = False,
) -> PairScore:
    matched = matched_signals(left, right)
    conflicts = calibrated_conflicting_signals(left, right, matched)
    weights = type_weights(pair_type(left, right))
    evidence_completeness = signal_evidence_completeness(matched, weights)
    score = pair_score(matched, weights, conflicts)
    decision, recommendation = pair_decision(
        score,
        evidence_completeness,
        previously_reviewed_not_duplicate,
        conflicts,
        matched,
    )
    return PairScore(
        left.id,
        right.id,
        score,
        decision,
        matched,
        conflicts,
        round(evidence_completeness, 4),
        build_reason(matched, conflicts, decision),
        recommendation,
        previously_reviewed_not_duplicate,
    )


def pair_score(
    matched: Mapping[str, Optional[float]],
    weights: Mapping[str, float],
    conflicts: Sequence[str],
) -> float:
    return round(
        adjust_identifier_score(
            weighted_match_score(matched, weights), matched, conflicts
        ),
        4,
    )


def build_reason(
    matched: Mapping[str, Optional[float]], conflicts: Sequence[str], decision: str
) -> str:
    strong = [
        field
        for field in ("doi", "isbn", "title", "contributors", "year", "containerTitle")
        if matched.get(field) is not None and (matched[field] or 0.0) >= 0.85
    ]
    if matched.get("issn") == 1.0 and "doi" not in strong and "isbn" not in strong:
        strong.append("issn-supporting")
    if conflicts:
        return (
            f"{decision}; strong signals: {', '.join(strong) or 'none'}; "
            f"conflicts: {', '.join(conflicts)}."
        )
    return f"{decision}; strong signals: {', '.join(strong) or 'none'}."
