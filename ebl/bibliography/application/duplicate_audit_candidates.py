from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from ebl.bibliography.application.duplicate_audit_normalization import (
    NormalizedBibliographyEntry,
)
from ebl.bibliography.application.duplicate_audit_scoring import PairScore, score_pair


def pair_key(left_id: str, right_id: str) -> tuple[str, str]:
    return tuple(sorted((left_id, right_id)))


def reviewed_not_duplicate_pairs(path: Optional[Path]) -> set[tuple[str, str]]:
    if not path or not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        pair_key(str(pair["leftId"]), str(pair["rightId"]))
        for pair in data.get("notDuplicatePairs", [])
    }


def group_by_exact(
    entries: Sequence[NormalizedBibliographyEntry], field_name: str
) -> dict[str, list[NormalizedBibliographyEntry]]:
    groups: dict[str, list[NormalizedBibliographyEntry]] = defaultdict(list)
    for entry in entries:
        value = getattr(entry, field_name)
        if value:
            groups[value].append(entry)
    return {key: value for key, value in groups.items() if len(value) > 1}


def generate_candidate_pairs(
    entries: Sequence[NormalizedBibliographyEntry],
    false_positive_pairs: set[tuple[str, str]] | None = None,
) -> list[PairScore]:
    false_positive_pairs = false_positive_pairs or set()
    by_id = {entry.id: entry for entry in entries}
    scored = [
        score_candidate_pair(pair, by_id, false_positive_pairs)
        for pair in candidate_pair_ids(entries)
    ]
    return sorted(
        [score for score in scored if is_reportable_pair(score)],
        key=lambda item: item.score,
        reverse=True,
    )


def candidate_pair_ids(
    entries: Sequence[NormalizedBibliographyEntry],
) -> set[tuple[str, str]]:
    candidate_ids: set[tuple[str, str]] = set()
    add_exact_identifier_pairs(candidate_ids, entries)
    add_bucket_pairs(candidate_ids, blocking_buckets(entries))
    return candidate_ids


def add_exact_identifier_pairs(
    candidate_ids: set[tuple[str, str]],
    entries: Sequence[NormalizedBibliographyEntry],
) -> None:
    for field_name in ("doi", "isbn", "issn"):
        for group in group_by_exact(entries, field_name).values():
            add_all_pairs(candidate_ids, [entry.id for entry in group])


def blocking_buckets(
    entries: Sequence[NormalizedBibliographyEntry],
) -> dict[tuple[Any, ...], list[str]]:
    buckets: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for entry in entries:
        add_entry_to_blocking_buckets(buckets, entry)
    return buckets


def add_entry_to_blocking_buckets(
    buckets: dict[tuple[Any, ...], list[str]], entry: NormalizedBibliographyEntry
) -> None:
    if entry.primary_family and entry.year is not None:
        buckets[("author_year", entry.primary_family, entry.year)].append(entry.id)
    if entry.year is not None:
        for token in sorted(entry.title_tokens):
            buckets[("year_title_token", entry.year, token)].append(entry.id)
    if entry.container_title and entry.year is not None:
        buckets[("container_year", entry.container_title, entry.year)].append(entry.id)
    if entry.title:
        buckets[("title_prefix", entry.title[:20])].append(entry.id)


def add_bucket_pairs(
    candidate_ids: set[tuple[str, str]],
    buckets: Mapping[tuple[Any, ...], Sequence[str]],
) -> None:
    for ids in buckets.values():
        if 1 < len(ids) <= 250:
            add_all_pairs(candidate_ids, ids)


def score_candidate_pair(
    pair: tuple[str, str],
    entries_by_id: Mapping[str, NormalizedBibliographyEntry],
    false_positive_pairs: set[tuple[str, str]],
) -> PairScore:
    left_id, right_id = pair
    return score_pair(
        entries_by_id[left_id],
        entries_by_id[right_id],
        previously_reviewed_not_duplicate=pair_key(left_id, right_id)
        in false_positive_pairs,
    )


def is_reportable_pair(score: PairScore) -> bool:
    return (
        score.score >= 0.70
        or score.decision in {"possible_duplicate", "likely_duplicate"}
        or score.previously_reviewed_not_duplicate
    )


def add_all_pairs(candidate_ids: set[tuple[str, str]], ids: Sequence[str]) -> None:
    candidate_ids.update(combinations(sorted(set(ids)), 2))
