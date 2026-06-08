from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.duplicate_audit import (
    PairScore,
    metadata_completeness,
    normalize_entry,
    score_pair,
)

DEFAULT_CANDIDATE_LIMIT = 10
MAX_CANDIDATE_LIMIT = 25
DEFAULT_CANDIDATE_POOL_LIMIT = 75


@dataclass(frozen=True)
class DuplicateDetectionResult:
    decision: str
    highest_score: float
    evidence_completeness: float
    candidates: Sequence[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "highestScore": self.highest_score,
            "evidenceCompleteness": self.evidence_completeness,
            "candidates": list(self.candidates),
        }


class BibliographyDuplicateDetector:
    def __init__(
        self,
        repository: BibliographyRepository,
        candidate_pool_limit: int = DEFAULT_CANDIDATE_POOL_LIMIT,
    ):
        self._repository = repository
        self._candidate_pool_limit = candidate_pool_limit

    def find_candidates(
        self, proposed_entry: Mapping[str, Any], limit: int = DEFAULT_CANDIDATE_LIMIT
    ) -> DuplicateDetectionResult:
        result_limit = max(1, min(limit, MAX_CANDIDATE_LIMIT))
        proposed = normalize_entry(proposed_entry)
        candidates = [
            normalize_entry(candidate)
            for candidate in self._repository.query_duplicate_candidates(
                proposed_entry, self._candidate_pool_limit
            )
        ]
        entries_by_id = {candidate.id: candidate for candidate in candidates}
        scored = sorted(
            (
                score_pair(proposed, candidate)
                for candidate in candidates
                if candidate.id and candidate.id != proposed.id
            ),
            key=lambda pair: pair.score,
            reverse=True,
        )
        reportable = [
            pair
            for pair in scored
            if pair.decision != "not_duplicate" or pair.score >= 0.70
        ][:result_limit]
        return DuplicateDetectionResult(
            decision=overall_decision(reportable),
            highest_score=reportable[0].score if reportable else 0.0,
            evidence_completeness=overall_evidence_completeness(
                proposed_entry, reportable
            ),
            candidates=[
                candidate_to_dict(pair, entries_by_id[pair.right_id])
                for pair in reportable
            ],
        )


def overall_decision(pairs: Sequence[PairScore]) -> str:
    decisions = {pair.decision for pair in pairs}
    if "likely_duplicate" in decisions:
        return "likely_duplicate"
    if "possible_duplicate" in decisions:
        return "possible_duplicate"
    if "insufficient_data" in decisions:
        return "insufficient_data"
    return "no_duplicate"


def overall_evidence_completeness(
    proposed_entry: Mapping[str, Any], pairs: Sequence[PairScore]
) -> float:
    if pairs:
        return max(pair.evidence_completeness for pair in pairs)
    return metadata_completeness(normalize_entry(proposed_entry))


def candidate_to_dict(pair: PairScore, candidate: Any) -> dict[str, Any]:
    return {
        "id": pair.right_id,
        "citationKey": candidate.raw.get("citationKey"),
        "score": pair.score,
        "decision": response_decision(pair.decision),
        "matchedFields": pair.matched_signals,
        "conflictingFields": pair.conflicting_signals,
        "evidenceCompleteness": pair.evidence_completeness,
        "recommendation": response_recommendation(pair.decision),
        "reason": pair.reason,
    }


def response_decision(decision: str) -> str:
    return "no_duplicate" if decision == "not_duplicate" else decision


def response_recommendation(decision: str) -> str:
    if decision == "likely_duplicate":
        return "block_or_request_override"
    if decision in {"possible_duplicate", "insufficient_data"}:
        return "confirm_before_create"
    return "allow_create"
