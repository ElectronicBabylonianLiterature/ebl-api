from typing import List
import attr

from ebl.transliteration.domain.museum_number import MuseumNumber

@attr.s(auto_attribs=True, frozen=True)
class QueryItem:
    _id: str
    museumNumber: MuseumNumber()
    matchingLines: List[int]
    total: int

class QueryResult:
    items: List[QueryItem]
    totalMatchingLines: int