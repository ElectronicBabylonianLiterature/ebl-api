from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

ARTICLE_LIKE_TYPES = {
    "article",
    "article-journal",
    "article-magazine",
    "article-newspaper",
    "chapter",
    "entry",
    "entry-dictionary",
    "entry-encyclopedia",
    "paper-conference",
    "review",
    "review-book",
}
BOOK_LIKE_TYPES = {"book", "thesis", "manuscript", "report"}
DEFAULT_WEIGHTS = {
    "title": 0.27,
    "contributors": 0.23,
    "year": 0.14,
    "containerTitle": 0.08,
    "publisher": 0.06,
    "collectionTitle": 0.05,
    "volume": 0.03,
    "issue": 0.02,
    "page": 0.02,
    "edition": 0.03,
    "language": 0.01,
    "type": 0.01,
    "issn": 0.03,
}
ARTICLE_WEIGHT_OVERRIDES = {
    "title": 0.24,
    "contributors": 0.20,
    "containerTitle": 0.13,
    "publisher": 0.03,
    "collectionTitle": 0.04,
    "volume": 0.06,
    "issue": 0.04,
    "page": 0.05,
    "edition": 0.01,
    "issn": 0.04,
}
BOOK_WEIGHT_OVERRIDES = {
    "title": 0.28,
    "contributors": 0.24,
    "containerTitle": 0.03,
    "publisher": 0.09,
    "volume": 0.02,
    "issue": 0.01,
    "page": 0.01,
    "edition": 0.05,
    "issn": 0.02,
}
PROJECTION = {
    "_id": 1,
    "type": 1,
    "title": 1,
    "title-short": 1,
    "author": 1,
    "editor": 1,
    "issued": 1,
    "DOI": 1,
    "ISBN": 1,
    "ISSN": 1,
    "language": 1,
    "container-title": 1,
    "container-title-short": 1,
    "collection-title": 1,
    "collection-number": 1,
    "publisher": 1,
    "volume": 1,
    "issue": 1,
    "page": 1,
    "page-first": 1,
    "edition": 1,
}


def normalize_doi(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip().casefold()
    value = re.sub(r"^doi:\s*", "", value)
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value.strip()


def normalize_identifier(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^0-9xX]", "", value).upper()


def normalize_isbn(value: Any) -> str:
    return normalize_identifier(value)


def normalize_issn(value: Any) -> str:
    return normalize_identifier(value)


def normalize_text(value: Any, *, fold_diacritics: bool = True) -> str:
    if not isinstance(value, str):
        return ""
    if fold_diacritics:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    else:
        value = unicodedata.normalize("NFKC", value)
    value = value.casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def normalize_short_field(value: Any) -> str:
    return normalize_text(str(value), fold_diacritics=True) if value is not None else ""


def title_tokens(title: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "der",
        "die",
        "das",
        "de",
        "des",
        "du",
        "for",
        "in",
        "of",
        "on",
        "the",
        "und",
        "von",
        "zu",
    }
    return {
        token for token in title.split() if len(token) > 1 and token not in stopwords
    }


def extract_year(entry: Mapping[str, Any]) -> Optional[int]:
    try:
        year = entry.get("issued", {}).get("date-parts", [[]])[0][0]
    except (IndexError, KeyError, TypeError):
        return None
    try:
        return int(year)
    except (TypeError, ValueError):
        return None


def normalize_name(name: Mapping[str, Any]) -> str:
    family = normalize_text(name.get("family"))
    literal = normalize_text(name.get("literal"))
    given = normalize_text(name.get("given"))
    initials = "".join(part[0] for part in given.split() if part)
    return "|".join(part for part in (family or literal, initials) if part)


def contributor_names(entry: Mapping[str, Any]) -> tuple[str, ...]:
    people = entry.get("author") or entry.get("editor") or ()
    return tuple(
        normalized for person in people if (normalized := normalize_name(person))
    )


def primary_family(entry: Mapping[str, Any]) -> str:
    names = contributor_names(entry)
    return names[0].split("|", 1)[0] if names else ""


@dataclass(frozen=True)
class NormalizedBibliographyEntry:
    id: str
    raw: Mapping[str, Any]
    type: str
    title: str
    title_tokens: set[str]
    contributors: tuple[str, ...]
    primary_family: str
    year: Optional[int]
    doi: str
    isbn: str
    issn: str
    container_title: str
    container_title_short: str
    collection_title: str
    publisher: str
    volume: str
    issue: str
    page: str
    page_first: str
    edition: str
    language: str


def normalize_entry(entry: Mapping[str, Any]) -> NormalizedBibliographyEntry:
    id_ = str(entry.get("_id") or entry.get("id") or "")
    normalized_title = normalize_text(entry.get("title"))
    return NormalizedBibliographyEntry(
        id=id_,
        raw=entry,
        type=str(entry.get("type") or ""),
        title=normalized_title,
        title_tokens=title_tokens(normalized_title),
        contributors=contributor_names(entry),
        primary_family=primary_family(entry),
        year=extract_year(entry),
        doi=normalize_doi(entry.get("DOI")),
        isbn=normalize_isbn(entry.get("ISBN")),
        issn=normalize_issn(entry.get("ISSN")),
        container_title=normalize_text(entry.get("container-title")),
        container_title_short=normalize_text(entry.get("container-title-short")),
        collection_title=normalize_text(entry.get("collection-title")),
        publisher=normalize_text(entry.get("publisher")),
        volume=normalize_short_field(entry.get("volume")),
        issue=normalize_short_field(entry.get("issue")),
        page=normalize_short_field(entry.get("page")),
        page_first=normalize_short_field(entry.get("page-first")),
        edition=normalize_short_field(entry.get("edition")),
        language=normalize_text(entry.get("language")),
    )


def ratio(left: str, right: str) -> Optional[float]:
    if not left or not right:
        return None
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


def token_overlap(left: set[str], right: set[str]) -> Optional[float]:
    if not left or not right:
        return None
    return len(left & right) / len(left | right)


def contributor_similarity(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> Optional[float]:
    if not left.contributors or not right.contributors:
        return None
    left_families = {name.split("|", 1)[0] for name in left.contributors}
    right_families = {name.split("|", 1)[0] for name in right.contributors}
    family_score = len(left_families & right_families) / len(
        left_families | right_families
    )
    if left.primary_family and left.primary_family == right.primary_family:
        family_score = max(family_score, 0.9)
    left_initials = left.contributors[0].split("|", 1)[1:] if left.contributors else []
    right_initials = (
        right.contributors[0].split("|", 1)[1:] if right.contributors else []
    )
    if left_initials and right_initials:
        if left_initials[0] == right_initials[0]:
            return min(1.0, family_score + 0.1)
        return max(0.0, family_score - 0.2)
    return family_score


def year_similarity(left: Optional[int], right: Optional[int]) -> Optional[float]:
    if left is None or right is None:
        return None
    if left == right:
        return 1.0
    if abs(left - right) == 1:
        return 0.35
    return 0.0


def exact_field_score(left: str, right: str) -> Optional[float]:
    if not left or not right:
        return None
    return 1.0 if left == right else 0.0


def field_score(left: str, right: str) -> Optional[float]:
    score = ratio(left, right)
    return None if score is None else score


def type_weights(entry_type: str) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    if entry_type in ARTICLE_LIKE_TYPES:
        weights.update(ARTICLE_WEIGHT_OVERRIDES)
    if entry_type in BOOK_LIKE_TYPES:
        weights.update(BOOK_WEIGHT_OVERRIDES)
    return weights


def pair_type(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> str:
    return left.type if left.type == right.type else left.type or right.type


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


def best_score(*scores: Optional[float]) -> Optional[float]:
    available = [score for score in scores if score is not None]
    return max(available) if available else None


def title_similarity(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> Optional[float]:
    if not left.title or not right.title:
        return None
    return best_score(
        ratio(left.title, right.title),
        token_overlap(left.title_tokens, right.title_tokens),
    )


def container_title_similarity(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> Optional[float]:
    return best_score(
        field_score(left.container_title, right.container_title),
        field_score(left.container_title_short, right.container_title_short),
    )


def page_similarity(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> Optional[float]:
    return best_score(
        exact_field_score(left.page, right.page),
        exact_field_score(left.page_first, right.page_first),
    )


def matched_signals(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> dict[str, Optional[float]]:
    return {
        "doi": exact_field_score(left.doi, right.doi),
        "isbn": exact_field_score(left.isbn, right.isbn),
        "issn": exact_field_score(left.issn, right.issn),
        "title": title_similarity(left, right),
        "contributors": contributor_similarity(left, right),
        "year": year_similarity(left.year, right.year),
        "containerTitle": container_title_similarity(left, right),
        "publisher": field_score(left.publisher, right.publisher),
        "collectionTitle": field_score(left.collection_title, right.collection_title),
        "volume": exact_field_score(left.volume, right.volume),
        "issue": exact_field_score(left.issue, right.issue),
        "page": page_similarity(left, right),
        "edition": exact_field_score(left.edition, right.edition),
        "language": exact_field_score(left.language, right.language),
        "type": exact_field_score(left.type, right.type),
    }


def conflicting_signals(matched: Mapping[str, Optional[float]]) -> list[str]:
    return [
        signal
        for signal in ("doi", "isbn", "year", "volume", "issue", "page", "edition")
        if matched.get(signal) == 0.0
    ]


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
    # ISSN is deliberately supporting evidence only.
    if matched["issn"] == 1.0 and score < 0.76:
        score = min(score + 0.06, 0.75)
    return score


def pair_decision(
    score: float,
    evidence_completeness: float,
    previously_reviewed_not_duplicate: bool,
) -> tuple[str, str]:
    if previously_reviewed_not_duplicate:
        return "not_duplicate", "ignore_previously_reviewed"
    if evidence_completeness < 0.35:
        return "insufficient_data", "manual_review_if_important"
    if score >= 0.92:
        return "likely_duplicate", "confirm_before_cleanup"
    if score >= 0.76:
        return "possible_duplicate", "review_before_create_or_cleanup"
    return "not_duplicate", "allow_create"


def score_pair(
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
    *,
    previously_reviewed_not_duplicate: bool = False,
) -> PairScore:
    matched = matched_signals(left, right)
    conflicts = conflicting_signals(matched)
    weights = type_weights(pair_type(left, right))
    evidence_completeness = signal_evidence_completeness(matched, weights)
    score = round(
        adjust_identifier_score(
            weighted_match_score(matched, weights), matched, conflicts
        ),
        4,
    )
    decision, recommendation = pair_decision(
        score, evidence_completeness, previously_reviewed_not_duplicate
    )
    reason = build_reason(matched, conflicts, decision)
    return PairScore(
        left.id,
        right.id,
        score,
        decision,
        matched,
        conflicts,
        round(evidence_completeness, 4),
        reason,
        recommendation,
        previously_reviewed_not_duplicate,
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
        return f"{decision}; strong signals: {', '.join(strong) or 'none'}; conflicts: {', '.join(conflicts)}."
    return f"{decision}; strong signals: {', '.join(strong) or 'none'}."


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
    unique_ids = sorted(set(ids))
    for index, left_id in enumerate(unique_ids):
        for right_id in unique_ids[index + 1 :]:
            candidate_ids.add((left_id, right_id))


@dataclass
class UsageCounts:
    fragments: int = 0
    corpus_texts: int = 0
    corpus_manuscripts: int = 0
    dossiers: int = 0
    note_markup: int = 0
    fully_checked: bool = True

    @property
    def total(self) -> int:
        return (
            self.fragments
            + self.corpus_texts
            + self.corpus_manuscripts
            + self.dossiers
            + self.note_markup
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "fragments": self.fragments,
            "corpusTexts": self.corpus_texts,
            "corpusManuscripts": self.corpus_manuscripts,
            "dossiers": self.dossiers,
            "noteMarkup": self.note_markup,
            "fullyChecked": self.fully_checked,
        }


def collect_usage_counts(database: Any, ids: Iterable[str]) -> dict[str, UsageCounts]:
    counts = {id_: UsageCounts() for id_ in ids}
    for id_ in counts:
        assign_count(
            counts[id_],
            "fragments",
            count_documents(database, "fragments", {"references.id": id_}),
        )
        assign_count(
            counts[id_],
            "corpus_texts",
            count_documents(database, "texts", {"references.id": id_}),
        )
        assign_count(
            counts[id_],
            "corpus_manuscripts",
            count_documents(
                database,
                "chapters",
                {
                    "$or": [
                        {"manuscripts.references.id": id_},
                        {"manuscripts.oldSigla.reference.id": id_},
                    ]
                },
            ),
        )
        assign_count(
            counts[id_],
            "dossiers",
            count_documents(database, "dossiers", {"references.id": id_}),
        )
    add_note_markup_counts(database, counts)
    return counts


def count_documents(
    database: Any, collection: str, query: Mapping[str, Any]
) -> Optional[int]:
    try:
        return database[collection].count_documents(query)
    except Exception:
        return None


def assign_count(usage: UsageCounts, field_name: str, count: Optional[int]) -> None:
    if count is None:
        usage.fully_checked = False
        setattr(usage, field_name, 0)
    else:
        setattr(usage, field_name, count)


def add_note_markup_counts(database: Any, counts: dict[str, UsageCounts]) -> None:
    if not counts:
        return
    pattern = re.compile(r"@bib\{([^@{}]+)")
    collections_and_fields = {
        "fragments": (
            "notes.text",
            "introduction.text",
            "text.lines.content.value",
        ),
        "chapters": (
            "lines.variants.note.parts.value",
            "manuscripts.notes",
        ),
        "texts": ("intro",),
    }
    for collection, fields in collections_and_fields.items():
        try:
            cursor = database[collection].find({}, dict.fromkeys(fields, 1))
        except Exception:
            for usage in counts.values():
                usage.fully_checked = False
            continue
        for document in cursor:
            for match in pattern.finditer(json.dumps(document, default=str)):
                id_ = match.group(1)
                if id_ in counts:
                    counts[id_].note_markup += 1


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


def cluster_pairs(
    pairs: Sequence[PairScore],
    entries_by_id: Mapping[str, NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts] | None = None,
) -> list[CandidateGroup]:
    usage_counts = dict(usage_counts or {})
    parents: dict[str, str] = {}

    def find(id_: str) -> str:
        parents.setdefault(id_, id_)
        if parents[id_] != id_:
            parents[id_] = find(parents[id_])
        return parents[id_]

    def union(left: str, right: str) -> None:
        parents[find(right)] = find(left)

    active_pairs = [
        pair
        for pair in pairs
        if pair.decision
        in {"likely_duplicate", "possible_duplicate", "insufficient_data"}
    ]
    for pair in active_pairs:
        union(pair.left_id, pair.right_id)

    groups: dict[str, list[str]] = defaultdict(list)
    for pair in active_pairs:
        groups[find(pair.left_id)].extend((pair.left_id, pair.right_id))

    candidate_groups = []
    for index, member_ids in enumerate(groups.values(), start=1):
        unique_member_ids = sorted(set(member_ids))
        group_pairs = [
            pair
            for pair in active_pairs
            if pair.left_id in unique_member_ids and pair.right_id in unique_member_ids
        ]
        canonical_id, reason = suggest_canonical(
            [entries_by_id[id_] for id_ in unique_member_ids], usage_counts
        )
        candidate_groups.append(
            CandidateGroup(
                f"BDG-{index:04}",
                unique_member_ids,
                group_pairs,
                canonical_id,
                reason,
                dict(usage_counts),
                entries_by_id,
            )
        )
    return sorted(candidate_groups, key=lambda group: group.highest_score, reverse=True)


def suggest_canonical(
    entries: Sequence[NormalizedBibliographyEntry],
    usage_counts: Mapping[str, UsageCounts] | None = None,
) -> tuple[str, str]:
    usage_counts_by_id = usage_counts or {}

    def score(entry: NormalizedBibliographyEntry) -> tuple[float, int, str]:
        identifier_bonus = 0.15 if entry.doi else 0.08 if entry.isbn else 0.0
        completeness = metadata_completeness(entry)
        usage = usage_counts_by_id.get(entry.id, UsageCounts()).total
        stable_id_bonus = 0.02 if re.match(r"^[A-Za-z0-9_.:-]+$", entry.id) else 0.0
        return (
            completeness + identifier_bonus + min(usage, 50) / 500 + stable_id_bonus,
            usage,
            entry.id,
        )

    winner = max(entries, key=score)
    usage = usage_counts_by_id.get(winner.id, UsageCounts()).total
    return (
        winner.id,
        f"Highest metadata completeness ({metadata_completeness(winner)}), "
        f"identifier strength ({'DOI' if winner.doi else 'ISBN' if winner.isbn else 'none'}), "
        f"and usage count ({usage}).",
    )


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
    score_buckets = Counter()
    for pair in pairs:
        bucket = (
            f"{int(pair.score * 10) / 10:.1f}-{int(pair.score * 10) / 10 + 0.1:.1f}"
        )
        score_buckets[bucket] += 1
    return {
        "totalRecordsScanned": len(entries),
        "missingTitle": sum(1 for entry in entries if not entry.title),
        "missingAuthorEditor": sum(1 for entry in entries if not entry.contributors),
        "missingYear": sum(1 for entry in entries if entry.year is None),
        "withDOI": sum(1 for entry in entries if entry.doi),
        "withISBN": sum(1 for entry in entries if entry.isbn),
        "withISSN": sum(1 for entry in entries if entry.issn),
        "exactDOIDuplicateGroups": len(group_by_exact(entries, "doi")),
        "exactISBNDuplicateGroups": len(group_by_exact(entries, "isbn")),
        "exactISSNSupportGroups": len(group_by_exact(entries, "issn")),
        "scoreDistribution": dict(sorted(score_buckets.items())),
    }


def write_reports(
    output_dir: Path,
    entries: Sequence[NormalizedBibliographyEntry],
    pairs: Sequence[PairScore],
    groups: Sequence[CandidateGroup],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = audit_statistics(entries, pairs)
    (output_dir / "bibliography_duplicate_candidate_groups.json").write_text(
        json.dumps([group.to_dict() for group in groups], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_pairs_csv(output_dir / "bibliography_duplicate_candidate_pairs.csv", pairs)
    write_groups_csv(output_dir / "bibliography_duplicate_candidate_groups.csv", groups)
    write_summary(output_dir / "bibliography_duplicate_audit_summary.md", stats, groups)


def write_pairs_csv(path: Path, pairs: Sequence[PairScore]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "leftId",
                "rightId",
                "score",
                "decision",
                "matchedSignals",
                "conflictingSignals",
                "evidenceCompleteness",
                "reason",
                "recommendation",
                "previouslyReviewedNotDuplicate",
            ],
        )
        writer.writeheader()
        for pair in pairs:
            row = pair_to_dict(pair)
            row["matchedSignals"] = json.dumps(row["matchedSignals"], sort_keys=True)
            row["conflictingSignals"] = ",".join(row["conflictingSignals"])
            writer.writerow(row)


def write_groups_csv(path: Path, groups: Sequence[CandidateGroup]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "candidateGroupId",
                "groupDecision",
                "highestScore",
                "averageScore",
                "memberIds",
                "suggestedCanonicalId",
                "canonicalReason",
                "needsHumanReview",
                "matchedSignalsSummary",
                "conflictingSignalsSummary",
            ],
        )
        writer.writeheader()
        for group in groups:
            data = group.to_dict()
            writer.writerow(
                {
                    **{
                        key: data[key]
                        for key in (
                            "candidateGroupId",
                            "groupDecision",
                            "highestScore",
                            "averageScore",
                            "suggestedCanonicalId",
                            "canonicalReason",
                            "needsHumanReview",
                        )
                    },
                    "memberIds": ",".join(data["memberIds"]),
                    "matchedSignalsSummary": json.dumps(
                        data["matchedSignalsSummary"], sort_keys=True
                    ),
                    "conflictingSignalsSummary": ",".join(
                        data["conflictingSignalsSummary"]
                    ),
                }
            )


def write_summary(
    path: Path, stats: Mapping[str, Any], groups: Sequence[CandidateGroup]
) -> None:
    likely = [group for group in groups if group.group_decision == "likely_duplicate"]
    possible = [
        group for group in groups if group.group_decision == "possible_duplicate"
    ]
    lines = [
        "# Bibliography Duplicate Audit Summary",
        "",
        "This report was generated by a read-only audit. It did not modify MongoDB records.",
        "",
        "## Calibration Metrics",
        "",
    ]
    for key, value in stats.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            f"- `fuzzyDuplicateGroups`: {len(groups)}",
            "",
            "## ISSN Handling",
            "",
            "Exact ISSN groups are serial/series support groups only. ISSN alone does not create a hard likely-duplicate decision.",
            "",
            "## Top Likely Duplicate Groups",
            "",
        ]
    )
    lines.extend(group_markdown(group) for group in likely[:10])
    lines.extend(["", "## Top Possible Duplicate Groups", ""])
    lines.extend(group_markdown(group) for group in possible[:10])
    lines.extend(
        [
            "",
            "## Recommended Thresholds",
            "",
            "Start review with `likely_duplicate >= 0.92` and `possible_duplicate >= 0.76`. Adjust after manual review of false positives, sparse records, and edition/variant cases.",
            "",
            "## Known Limitations",
            "",
            "- Note-markup usage is best-effort and may miss dynamically generated or differently serialized `@bib{}` references.",
            "- The offline detector uses broader blocking than a future online API should use.",
            "- No merge, deprecation, or tombstone workflow is implemented here.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def group_markdown(group: CandidateGroup) -> str:
    return (
        f"- `{group.group_id}` {group.group_decision}, highest={group.highest_score}, "
        f"members={', '.join(group.member_ids)}, canonical={group.suggested_canonical_id}"
    )


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
