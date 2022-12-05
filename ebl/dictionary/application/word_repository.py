from abc import ABC, abstractmethod
from typing import Sequence

from ebl.dictionary.domain.word import WordId


class WordRepository(ABC):
    @abstractmethod
    def create(self, word) -> WordId:
        ...

    @abstractmethod
    def query_by_id(self, id_: WordId):
        ...

    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence:
        ...

    @abstractmethod
    def query_by_lemma_form_or_meaning(self, query: str) -> Sequence:
        ...

    @abstractmethod
    def query_by_lemma_prefix(self, query: str) -> Sequence:
        ...

    @abstractmethod
    def update(self, word) -> None:
        ...
