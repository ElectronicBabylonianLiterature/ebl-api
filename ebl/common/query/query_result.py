from typing import Sequence
import attr

from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class QueryItem:
    id_: str
    museum_number: MuseumNumber
    matching_lines: Sequence[int]
    match_count: int


@attr.s(auto_attribs=True, frozen=True)
class QueryResult:
    items: Sequence[QueryItem]
    match_count_total: int
