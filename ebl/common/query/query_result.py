from typing import Sequence
import attr
from ebl.fragmentarium.infrastructure.phrase_matcher import LemmaSequence

from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class QueryItem:
    id_: str
    museum_number: MuseumNumber
    matching_lines: Sequence[int]
    match_count: int
    lemma_sequences: Sequence[LemmaSequence] = tuple()


@attr.s(auto_attribs=True, frozen=True)
class QueryResult:
    items: Sequence[QueryItem]
    match_count_total: int
