from typing import Optional, Sequence
import attr
from enum import Enum
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


def _query_result_equality_values(result):
    return (
        tuple(result.items),
        result.match_count_total,
        result.is_match_count_total_exact,
        result.has_next_page,
    )


def compare_query_results(left, right):
    try:
        right_values = (
            tuple(right.items),
            right.match_count_total,
            getattr(right, "is_match_count_total_exact", True),
            getattr(right, "has_next_page", None),
        )
    except AttributeError:
        return NotImplemented

    return _query_result_equality_values(left) == right_values


class LemmaQueryType(Enum):
    AND = "and"
    OR = "or"
    LINE = "line"
    PHRASE = "phrase"


@attr.s(auto_attribs=True, frozen=True)
class QueryItem:
    museum_number: MuseumNumber
    matching_lines: Sequence[int]
    match_count: int


@attr.s(auto_attribs=True, frozen=True, eq=False)
class QueryResult:
    items: Sequence[QueryItem]
    match_count_total: Optional[int]
    is_match_count_total_exact: bool = True
    has_next_page: Optional[bool] = None

    @staticmethod
    def create_empty() -> "QueryResult":
        return QueryResult([], 0)

    def __eq__(self, other):
        return compare_query_results(self, other)


@attr.s(auto_attribs=True, frozen=True)
class CorpusQueryItem:
    text_id: TextId
    stage: Stage
    name: str
    lines: Sequence[int]
    variants: Sequence[int]
    match_count: int


@attr.s(auto_attribs=True, frozen=True)
class AfORegisterToFragmentQueryItem:
    traditional_reference: str
    fragment_numbers: Sequence[str]


@attr.s(auto_attribs=True, frozen=True)
class CorpusQueryResult:
    items: Sequence[CorpusQueryItem]
    match_count_total: Optional[int]
    is_match_count_total_exact: bool = True
    has_next_page: Optional[bool] = None

    @staticmethod
    def create_empty() -> "CorpusQueryResult":
        return CorpusQueryResult([], 0)


@attr.s(auto_attribs=True, frozen=True)
class AfORegisterToFragmentQueryResult:
    items: Sequence[AfORegisterToFragmentQueryItem]

    @staticmethod
    def create_empty() -> "AfORegisterToFragmentQueryResult":
        return AfORegisterToFragmentQueryResult([])
