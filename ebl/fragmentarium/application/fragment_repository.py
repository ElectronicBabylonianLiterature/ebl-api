from abc import ABC, abstractmethod
from typing import List

from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.transliteration_query import TransliterationQuery


class FragmentRepository(ABC):
    @abstractmethod
    def create(self, fragment: Fragment) -> FragmentNumber:
        ...

    @abstractmethod
    def count_transliterated_fragments(self) -> int:
        ...

    @abstractmethod
    def count_lines(self) -> int:
        ...

    @abstractmethod
    def query_by_fragment_number(self, number: FragmentNumber) -> Fragment:
        ...

    @abstractmethod
    def query_by_fragment_cdli_or_accession_number(self, number: str) -> List[Fragment]:
        ...

    @abstractmethod
    def query_random_by_transliterated(self) -> List[Fragment]:
        ...

    @abstractmethod
    def query_path_of_the_pioneers(self,) -> List[Fragment]:
        ...

    @abstractmethod
    def query_by_transliterated_sorted_by_date(self) -> List[Fragment]:
        ...

    @abstractmethod
    def query_by_transliterated_not_revised_by_other(self,) -> List[FragmentInfo]:
        ...

    @abstractmethod
    def query_by_transliteration(self, query: TransliterationQuery) -> List[Fragment]:
        ...

    @abstractmethod
    def query_transliterated_numbers(self) -> List[str]:
        ...

    @abstractmethod
    def query_next_and_previous_folio(
        self, folio_name: str, folio_number: str, number: FragmentNumber
    ) -> dict:
        ...

    @abstractmethod
    def query_next_and_previous_fragment(self, number: FragmentNumber) -> dict:
        ...

    @abstractmethod
    def query_lemmas(self, word: str) -> List[List[dict]]:
        ...

    @abstractmethod
    def update_transliteration(self, fragment: Fragment) -> None:
        ...

    @abstractmethod
    def update_lemmatization(self, fragment: Fragment) -> None:
        ...

    @abstractmethod
    def update_references(self, fragment: Fragment) -> None:
        ...
