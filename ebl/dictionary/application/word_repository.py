from abc import ABC, abstractmethod
from typing import Sequence, Optional
from ebl.dictionary.domain.dictionary_query import DictionaryFieldQuery

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
    def query_by_lemma_meaning_root_vowels(
        self,
        word: Optional[DictionaryFieldQuery],
        meaning: Optional[DictionaryFieldQuery],
        root: Optional[DictionaryFieldQuery],
        vowelClass: Optional[DictionaryFieldQuery],
    ) -> Sequence:
        ...

    @abstractmethod
    def query_by_lemma_prefix(self, query: str) -> Sequence:
        ...

    @abstractmethod
    def update(self, word) -> None:
        ...
