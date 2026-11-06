from types import NotImplementedType
from typing import Optional, Protocol, Sequence, cast
import attr
from enum import Enum
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


class _QueryResultValue(Protocol):
    items: Sequence[object]
    match_count_total: Optional[int]


def _query_result_equality_values(result: object) -> tuple:
    query_result = cast(_QueryResultValue, result)
    return (
        tuple(query_result.items),
        query_result.match_count_total,
        getattr(result, "is_match_count_total_exact", True),
        getattr(result, "has_next_page", None),
        getattr(result, "total_documents", None),
    )


def compare_query_results(left: object, right: object) -> bool | NotImplementedType:
    try:
        return _query_result_equality_values(left) == _query_result_equality_values(
            right
        )
    except AttributeError:
        return NotImplemented


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
    total_documents: Optional[int] = None

    @staticmethod
    def create_empty() -> "QueryResult":
        return QueryResult([], 0, total_documents=0)

    def __eq__(self, other: object) -> bool | NotImplementedType:
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
    total_chapters: Optional[int] = None

    @staticmethod
    def create_empty() -> "CorpusQueryResult":
        return CorpusQueryResult([], 0)


@attr.s(auto_attribs=True, frozen=True)
class AfORegisterToFragmentQueryResult:
    items: Sequence[AfORegisterToFragmentQueryItem]

    @staticmethod
    def create_empty() -> "AfORegisterToFragmentQueryResult":
        return AfORegisterToFragmentQueryResult([])
