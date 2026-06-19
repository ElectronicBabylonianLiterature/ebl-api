from __future__ import annotations

from difflib import SequenceMatcher
from typing import Optional

from ebl.bibliography.application.duplicate_audit_normalization import (
    NormalizedBibliographyEntry,
)

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


def ratio(left: str, right: str) -> Optional[float]:
    if not left or not right:
        return None
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


def jaccard(left: set[str], right: set[str]) -> Optional[float]:
    if not left or not right:
        return None
    return len(left & right) / len(left | right)


def token_overlap(left: set[str], right: set[str]) -> Optional[float]:
    return jaccard(left, right)


def contributor_similarity(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> Optional[float]:
    if not left.contributors or not right.contributors:
        return None
    family_score = contributor_family_score(left, right)
    return adjust_for_primary_initials(family_score, left, right)


def contributor_family_score(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> float:
    family_score = jaccard(contributor_families(left), contributor_families(right))
    score = family_score or 0.0
    if left.primary_family and left.primary_family == right.primary_family:
        return max(score, 0.9)
    return score


def contributor_families(entry: NormalizedBibliographyEntry) -> set[str]:
    return {name.split("|", 1)[0] for name in entry.contributors}


def adjust_for_primary_initials(
    family_score: float,
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
) -> float:
    left_initials = primary_initials(left)
    right_initials = primary_initials(right)
    if left_initials and right_initials:
        if left_initials == right_initials:
            return min(1.0, family_score + 0.1)
        return max(0.0, family_score - 0.2)
    return family_score


def primary_initials(entry: NormalizedBibliographyEntry) -> str:
    if not entry.contributors:
        return ""
    parts = entry.contributors[0].split("|", 1)
    return parts[1] if len(parts) > 1 else ""


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
