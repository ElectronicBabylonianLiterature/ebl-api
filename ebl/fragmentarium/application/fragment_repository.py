from abc import ABC, abstractmethod
from typing import List

from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.transliteration_query import \
    TransliterationQuery


class FragmentRepository(ABC):
    @abstractmethod
    def create(self, fragment: Fragment) -> FragmentNumber:
        ...

    @abstractmethod
    def find(self, number: FragmentNumber) -> Fragment:
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

    @abstractmethod
    def count_transliterated_fragments(self) -> int:
        ...

    @abstractmethod
    def count_lines(self) -> int:
        ...

    @abstractmethod
    def search(self, number: str) -> List[Fragment]:
        ...

    @abstractmethod
    def find_random(self) -> List[Fragment]:
        ...

    @abstractmethod
    def find_interesting(self) -> List[Fragment]:
        ...

    @abstractmethod
    def find_latest(self) -> List[Fragment]:
        ...

    @abstractmethod
    def find_needs_revision(self) -> List[FragmentInfo]:
        ...

    @abstractmethod
    def search_signs(self, query: TransliterationQuery) -> List[Fragment]:
        ...

    @abstractmethod
    def folio_pager(self,
                    folio_name: str,
                    folio_number: str,
                    number: FragmentNumber) -> dict:
        ...

    @abstractmethod
    def find_lemmas(self, word: str) -> List[List[dict]]:
        ...
