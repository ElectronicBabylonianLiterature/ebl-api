from abc import ABC, abstractmethod
from typing import List, Sequence, Optional
from ebl.common.query.query_result import QueryResult

from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
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
    def query_by_museum_number(
        self, number: MuseumNumber, lines: Optional[Sequence[int]] = None
    ) -> Fragment:
        ...

    @abstractmethod
    def query_random_by_transliterated(
        self, user_scopes: Optional[List[str]]
    ) -> List[Fragment]:
        ...

    @abstractmethod
    def query_path_of_the_pioneers(
        self, user_scopes: Optional[List[str]]
    ) -> List[Fragment]:
        ...

    @abstractmethod
    def query_by_transliterated_sorted_by_date(
        self, user_scopes: Optional[List[str]]
    ) -> List[Fragment]:
        ...

    @abstractmethod
    def query_by_transliterated_not_revised_by_other(
        self, user_scopes: Optional[List[str]]
    ) -> List[FragmentInfo]:
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

    @abstractmethod
    def query(self, query: dict) -> QueryResult:
        ...

    @abstractmethod
    def fetch_scopes(self, number: MuseumNumber) -> List[str]:
        ...
