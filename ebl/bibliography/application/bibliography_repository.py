from abc import ABC, abstractmethod
from typing import Optional


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
    def query_by_author_year_and_title(self,
                                       author: Optional[str],
                                       year: Optional[str],
                                       title: Optional[str]):
        ...
