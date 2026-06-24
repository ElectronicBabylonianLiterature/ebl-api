from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ebl.bibliography.application.duplicate_audit_candidates import pair_key
from ebl.bibliography.application.duplicate_audit_normalization import (
    NormalizedBibliographyEntry,
)
from ebl.bibliography.application.duplicate_audit_scoring import PairScore
from ebl.bibliography.application.duplicate_audit_summary import (
    member_summary,
    pair_to_dict,
    summarize_signals,
    suggest_canonical,
)
from ebl.bibliography.application.duplicate_audit_usage import UsageCounts


@dataclass
class CandidateGroup:
    group_id: str
    member_ids: list[str]
    pair_scores: list[PairScore]
    suggested_canonical_id: str
    canonical_reason: str
    usage_counts: dict[str, UsageCounts]
    entries_by_id: Mapping[str, NormalizedBibliographyEntry]

    @property
    def highest_score(self) -> float:
        return max(pair.score for pair in self.pair_scores)

    @property
    def average_score(self) -> float:
        return round(
            sum(pair.score for pair in self.pair_scores) / len(self.pair_scores), 4
        )

    @property
    def group_decision(self) -> str:
        decisions = {pair.decision for pair in self.pair_scores}
        if "likely_duplicate" in decisions:
            return "likely_duplicate"
        if "possible_duplicate" in decisions:
            return "possible_duplicate"
        if "insufficient_data" in decisions:
            return "insufficient_data"
        return "not_duplicate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidateGroupId": self.group_id,
            "groupDecision": self.group_decision,
            "highestScore": self.highest_score,
            "averageScore": self.average_score,
            "memberIds": self.member_ids,
            "suggestedCanonicalId": self.suggested_canonical_id,
            "canonicalReason": self.canonical_reason,
            "needsHumanReview": self.group_decision != "not_duplicate",
            "matchedSignalsSummary": summarize_signals(
                pair.matched_signals for pair in self.pair_scores
            ),
            "conflictingSignalsSummary": sorted(
                {
                    signal
                    for pair in self.pair_scores
                    for signal in pair.conflicting_signals
                }
            ),
            "groupMembers": [
                member_summary(
                    self.entries_by_id[id_],
                    self.usage_counts.get(id_, UsageCounts()),
                )
                for id_ in self.member_ids
            ],
            "pairs": [pair_to_dict(pair) for pair in self.pair_scores],
        }


class _UnionFind:
    def __init__(self) -> None:
        self._parents: dict[str, str] = {}

    def find(self, id_: str) -> str:
        self._parents.setdefault(id_, id_)
        if self._parents[id_] != id_:
            self._parents[id_] = self.find(self._parents[id_])
        return self._parents[id_]

    def union(self, left: str, right: str) -> None:
        self._parents[self.find(right)] = self.find(left)


def cluster_pairs(
    pairs: Sequence[PairScore],
    entries_by_id: Mapping[str, NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts] | None = None,
) -> list[CandidateGroup]:
    usage_counts_by_id = dict(usage_counts or {})
    active_pairs = [pair for pair in pairs if is_active_pair(pair)]
    link_pairs = [pair for pair in active_pairs if can_link_candidate_group(pair)]
    grouped_members = linked_member_groups(link_pairs)
    candidate_groups = grouped_candidate_groups(
        grouped_members, link_pairs, entries_by_id, usage_counts_by_id
    )
    represented = represented_pair_keys(candidate_groups)
    candidate_groups.extend(
        unrepresented_pair_groups(
            active_pairs, represented, entries_by_id, usage_counts_by_id
        )
    )
    return assign_group_ids(candidate_groups)


def is_active_pair(pair: PairScore) -> bool:
    return pair.decision in {
        "likely_duplicate",
        "possible_duplicate",
        "insufficient_data",
    }


def linked_member_groups(link_pairs: Sequence[PairScore]) -> list[list[str]]:
    union_find = _UnionFind()
    for pair in link_pairs:
        union_find.union(pair.left_id, pair.right_id)
    groups: dict[str, list[str]] = defaultdict(list)
    for pair in link_pairs:
        groups[union_find.find(pair.left_id)].extend((pair.left_id, pair.right_id))
    return list(groups.values())


def grouped_candidate_groups(
    grouped_members: Sequence[Sequence[str]],
    link_pairs: Sequence[PairScore],
    entries_by_id: Mapping[str, NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts],
) -> list[CandidateGroup]:
    return [
        build_candidate_group(
            unique_member_ids,
            [
                pair
                for pair in link_pairs
                if pair.left_id in unique_member_ids
                and pair.right_id in unique_member_ids
            ],
            entries_by_id,
            usage_counts,
        )
        for member_ids in grouped_members
        if (unique_member_ids := sorted(set(member_ids)))
    ]


def represented_pair_keys(groups: Sequence[CandidateGroup]) -> set[tuple[str, str]]:
    return {
        pair_key(pair.left_id, pair.right_id)
        for group in groups
        for pair in group.pair_scores
    }


def unrepresented_pair_groups(
    active_pairs: Sequence[PairScore],
    represented: set[tuple[str, str]],
    entries_by_id: Mapping[str, NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts],
) -> list[CandidateGroup]:
    return [
        build_candidate_group(
            sorted([pair.left_id, pair.right_id]),
            [pair],
            entries_by_id,
            usage_counts,
        )
        for pair in active_pairs
        if pair_key(pair.left_id, pair.right_id) not in represented
    ]


def assign_group_ids(groups: Sequence[CandidateGroup]) -> list[CandidateGroup]:
    sorted_groups = sorted(groups, key=lambda group: group.highest_score, reverse=True)
    for index, group in enumerate(sorted_groups, start=1):
        group.group_id = f"BDG-{index:04}"
    return sorted_groups


def can_link_candidate_group(pair: PairScore) -> bool:
    if has_disqualifying_group_conflict(pair):
        return False
    title_score = pair.matched_signals.get("title") or 0.0
    if title_score < 0.50:
        return False
    if pair.decision == "likely_duplicate":
        return True
    return (
        pair.decision == "possible_duplicate"
        and pair.score >= 0.76
        and title_score >= 0.70
    )


def has_disqualifying_group_conflict(pair: PairScore) -> bool:
    return bool(
        {
            "series_part",
            "different_title",
            "different_page",
            "different_volume",
            "different_issue",
            "different_entry_title",
            "different_webpage_title",
            "doi_data_issue",
        }.intersection(pair.conflicting_signals)
    )


def build_candidate_group(
    member_ids: Sequence[str],
    group_pairs: Sequence[PairScore],
    entries_by_id: Mapping[str, NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts],
) -> CandidateGroup:
    canonical_id, reason = suggest_canonical(
        [entries_by_id[id_] for id_ in member_ids], usage_counts
    )
    return CandidateGroup(
        "",
        list(member_ids),
        list(group_pairs),
        canonical_id,
        reason,
        dict(usage_counts),
        entries_by_id,
    )
