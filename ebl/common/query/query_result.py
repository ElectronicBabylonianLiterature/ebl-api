from typing import Optional, Sequence
import attr
from enum import Enum
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


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
    show_count_metadata: bool = False

    @staticmethod
    def create_empty() -> "QueryResult":
        return QueryResult([], 0)

    def __eq__(self, other):
        if isinstance(other, QueryResult):
            return (
                tuple(self.items) == tuple(other.items)
                and self.match_count_total == other.match_count_total
                and self.is_match_count_total_exact
                == other.is_match_count_total_exact
                and self.has_next_page == other.has_next_page
            )

        try:
            other_items = other.items
            other_match_count_total = other.match_count_total
        except AttributeError:
            return NotImplemented

        return (
            tuple(self.items) == tuple(other_items)
            and self.match_count_total == other_match_count_total
            and self.is_match_count_total_exact
            == getattr(other, "is_match_count_total_exact", True)
            and self.has_next_page == getattr(other, "has_next_page", None)
        )


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
    show_count_metadata: bool = False

    @staticmethod
    def create_empty() -> "CorpusQueryResult":
        return CorpusQueryResult([], 0)


@attr.s(auto_attribs=True, frozen=True)
class AfORegisterToFragmentQueryResult:
    items: Sequence[AfORegisterToFragmentQueryItem]

    @staticmethod
    def create_empty() -> "AfORegisterToFragmentQueryResult":
        return AfORegisterToFragmentQueryResult([])
