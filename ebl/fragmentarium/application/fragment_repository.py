from abc import ABC, abstractmethod
from typing import List, Sequence, Optional, Union
from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryResult, AfORegisterToFragmentQueryResult

from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.date import Date


class FragmentRepository(ABC):
    @abstractmethod
    def create_indexes(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def create(self, fragment: Fragment, sort_key: Optional[int] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_many(self, fragments: Sequence[Fragment]) -> Sequence[str]:
        raise NotImplementedError

    @abstractmethod
    def count_transliterated_fragments(self, only_authorized: bool = True) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_lines(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_total_fragments(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def query_by_museum_number(
        self,
        number: Union[MuseumNumber, ExcavationNumber],
        lines: Optional[Sequence[int]] = None,
        exclude_lines: bool = False,
    ) -> Fragment:
        raise NotImplementedError

    @abstractmethod
    def query_by_traditional_references(
        self,
        traditional_references: Sequence[str],
        user_scopes: Sequence[Scope],
    ) -> AfORegisterToFragmentQueryResult:
        raise NotImplementedError

    @abstractmethod
    def query_random_by_transliterated(
        self, user_scopes: Sequence[Scope]
    ) -> List[Fragment]:
        raise NotImplementedError

    @abstractmethod
    def query_path_of_the_pioneers(
        self, user_scopes: Sequence[Scope]
    ) -> List[Fragment]:
        raise NotImplementedError

    @abstractmethod
    def query_by_transliterated_not_revised_by_other(
        self, user_scopes: Sequence[Scope]
    ) -> List[FragmentInfo]:
        raise NotImplementedError

    @abstractmethod
    def query_transliterated_numbers(self) -> List[MuseumNumber]:
        raise NotImplementedError

    @abstractmethod
    def query_transliterated_line_to_vec(
        self,
    ) -> List[LineToVecEntry]:
        raise NotImplementedError

    @abstractmethod
    def query_next_and_previous_folio(
        self, folio_name: str, folio_number: str, number: MuseumNumber
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def query_next_and_previous_fragment(
        self, museum_number: MuseumNumber
    ) -> FragmentPagerInfo:
        raise NotImplementedError

    @abstractmethod
    def update_field(self, field: str, fragment: Fragment) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, query: dict, user_scopes: Sequence[Scope] = ()) -> QueryResult:
        raise NotImplementedError

    @abstractmethod
    def query_latest(self) -> QueryResult:
        raise NotImplementedError

    @abstractmethod
    def fetch_scopes(self, number: MuseumNumber) -> List[Scope]:
        raise NotImplementedError

    @abstractmethod
    def fetch_names(self, name_query: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def fetch_date(self, number: MuseumNumber) -> Optional[Date]:
        raise NotImplementedError

    @abstractmethod
    def list_all_fragments(self) -> Sequence[str]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_transliterated_fragments(self, skip: int) -> Sequence[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_fragment_signs(self) -> Sequence[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_fragment_ocred_signs(self) -> Sequence[dict]:
        raise NotImplementedError

    @abstractmethod
    def collect_lemmas(self, number: MuseumNumber) -> dict:
        raise NotImplementedError
