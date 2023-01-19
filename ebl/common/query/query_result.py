from typing import Sequence
import attr
from enum import Enum

from ebl.transliteration.domain.museum_number import MuseumNumber


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


@attr.s(auto_attribs=True, frozen=True)
class QueryResult:
    items: Sequence[QueryItem]
    match_count_total: int

    @staticmethod
    def create_empty() -> "QueryResult":
        return QueryResult([], 0)
