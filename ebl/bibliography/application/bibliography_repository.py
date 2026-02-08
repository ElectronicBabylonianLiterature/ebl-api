from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence


class BibliographyRepository(ABC):
    @abstractmethod
    def create(self, entry: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    def query_by_id(self, id_: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def update(self, entry: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def list_all_bibliography(self) -> Sequence[Any]:
        raise NotImplementedError
