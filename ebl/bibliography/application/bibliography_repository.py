from abc import ABC, abstractmethod
from typing import Optional, Sequence


class BibliographyRepository(ABC):
    @abstractmethod
    def create(self, entry) -> str:
        ...

    @abstractmethod
    def query_by_id(self, id_: str):
        ...

    @abstractmethod
    def update(self, entry) -> None:
        ...

    @abstractmethod
    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ):
        ...

    @abstractmethod
    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ):
        ...

    @abstractmethod
    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ):
        ...

    @abstractmethod
    def list_all_bibliography(self) -> Sequence:
        ...

    @abstractmethod
    def list_all_indexed_bibliography(self) -> Sequence:
        ...
