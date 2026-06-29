import re
from typing import Mapping, Optional, Sequence, Tuple, cast

from ebl.common.query.query_collation import CollatedFieldQuery

EXACT_RANK = 0
PREFIX_RANK = 1
SUBSTRING_RANK = 2
TERM_RANK_OFFSET = 3
NO_MATCH_RANK = 6

RICHNESS_LIST_FIELDS = (
    "relatedTerms",
    "type",
    "afoRegister",
    "references",
    "wikidataId",
)


class _FieldMatcher:
    def __init__(self, pattern: str) -> None:
        self._exact = re.compile(f"^(?:{pattern})$", re.IGNORECASE)
        self._prefix = re.compile(f"^(?:{pattern})", re.IGNORECASE)
        self._substring = re.compile(pattern, re.IGNORECASE)

    def rank(self, text: str) -> Optional[int]:
        if self._exact.match(text):
            return EXACT_RANK
        if self._prefix.match(text):
            return PREFIX_RANK
        if self._substring.search(text):
            return SUBSTRING_RANK
        return None


class RealiaRelevanceRanker:
    def __init__(self, query: str) -> None:
        self._id_matcher = _FieldMatcher(
            CollatedFieldQuery(query, "_id", "realia").value
        )
        self._term_matcher = _FieldMatcher(
            CollatedFieldQuery(query, "relatedTerms", "realia").value
        )

    def key(self, document: Mapping[str, object]) -> Tuple[int, int, str, str]:
        identifier = cast(str, document["_id"])
        return (
            self._rank(identifier, document),
            -self._data_richness(document),
            identifier.casefold(),
            identifier,
        )

    def _data_richness(self, document: Mapping[str, object]) -> int:
        total = 0
        for field in RICHNESS_LIST_FIELDS:
            value = document.get(field)
            if isinstance(value, list):
                total += len(value)
        if document.get("reallexikon"):
            total += 1
        return total

    def _rank(self, identifier: str, document: Mapping[str, object]) -> int:
        id_rank = self._id_matcher.rank(identifier)
        if id_rank is not None:
            return id_rank
        raw_related_terms = document.get("relatedTerms", [])
        related_terms = (
            cast(Sequence[str], raw_related_terms)
            if isinstance(raw_related_terms, list)
            else []
        )
        term_ranks = [
            rank
            for rank in (self._term_matcher.rank(term) for term in related_terms)
            if rank is not None
        ]
        return TERM_RANK_OFFSET + min(term_ranks) if term_ranks else NO_MATCH_RANK
