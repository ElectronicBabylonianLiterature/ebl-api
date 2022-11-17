from abc import ABC, abstractmethod
from typing import List, Sequence, Tuple

from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.fragmentarium.application.fragmentarium_search_query import (
    FragmentariumSearchQuery,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


class FragmentRepository(ABC):
    @abstractmethod
    def create_indexes(self) -> None:
        ...

    @abstractmethod
    def create(self, fragment: Fragment) -> str:
        ...

    @abstractmethod
    def create_many(self, fragments: Sequence[Fragment]) -> Sequence[str]:
        ...

    @abstractmethod
    def count_transliterated_fragments(self) -> int:
        ...

    @abstractmethod
    def count_lines(self) -> int:
        ...

    @abstractmethod
    def query_by_museum_number(self, number: MuseumNumber) -> Fragment:
        ...

    @abstractmethod
    def query_random_by_transliterated(self) -> List[Fragment]:
        ...

    @abstractmethod
    def query_path_of_the_pioneers(self) -> List[Fragment]:
        ...

    @abstractmethod
    def query_by_transliterated_sorted_by_date(self) -> List[Fragment]:
        ...

    @abstractmethod
    def query_by_transliterated_not_revised_by_other(self) -> List[FragmentInfo]:
        ...

    @abstractmethod
    def query_transliterated_numbers(self) -> List[MuseumNumber]:
        ...

    @abstractmethod
    def query_transliterated_line_to_vec(
        self,
    ) -> List[LineToVecEntry]:
        ...

    @abstractmethod
    def query_next_and_previous_folio(
        self, folio_name: str, folio_number: str, number: MuseumNumber
    ) -> dict:
        ...

    @abstractmethod
    def query_next_and_previous_fragment(
        self, museum_number: MuseumNumber
    ) -> FragmentPagerInfo:
        ...

    @abstractmethod
    def update_field(self, field: str, fragment: Fragment) -> None:
        ...

    def query_fragmentarium(
        self, query: FragmentariumSearchQuery
    ) -> Tuple[Sequence[Fragment], int]:
        ...
