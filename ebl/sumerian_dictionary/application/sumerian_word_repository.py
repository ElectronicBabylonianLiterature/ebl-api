from abc import ABC, abstractmethod
from typing import Sequence

from ebl.sumerian_dictionary.domain.search_query import SumerianWordQuery
from ebl.sumerian_dictionary.domain.sumerian_word import SumerianWord
from ebl.sumerian_dictionary.domain.sumerian_word_summary import (
    SearchResult,
    Statistics,
    SumerianWordSummary,
)


class SumerianWordRepository(ABC):
    @abstractmethod
    def create_indexes(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def find(self, id_: str) -> SumerianWord:
        raise NotImplementedError()

    @abstractmethod
    def search(self, query: SumerianWordQuery) -> SearchResult:
        raise NotImplementedError()

    @abstractmethod
    def find_summaries(self, ids: Sequence[str]) -> Sequence[SumerianWordSummary]:
        raise NotImplementedError()

    @abstractmethod
    def list_ids(self) -> Sequence[str]:
        raise NotImplementedError()

    @abstractmethod
    def statistics(self) -> Statistics:
        raise NotImplementedError()
