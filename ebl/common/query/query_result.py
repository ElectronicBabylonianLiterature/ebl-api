from typing import Sequence
import attr
from ebl.fragmentarium.infrastructure.phrase_matcher import LemmaLine

from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class QueryItem:
    id_: str
    museum_number: MuseumNumber
    matching_lines: Sequence[int]
    total: int
    lemma_sequences: Sequence[LemmaLine] = attr.ib(default=tuple())


@attr.s(auto_attribs=True, frozen=True)
class QueryResult:
    items: Sequence[QueryItem]
    total_matching_lines: int
