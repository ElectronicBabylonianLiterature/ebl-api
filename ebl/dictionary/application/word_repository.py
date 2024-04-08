from abc import ABC, abstractmethod
from typing import Sequence, Optional
from ebl.common.query.query_collation import CollatedFieldQuery

from ebl.dictionary.domain.word import WordId


class WordRepository(ABC):
    @abstractmethod
    def create(self, word) -> WordId: ...

    @abstractmethod
    def query_by_id(self, id_: WordId): ...

    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence: ...

    @abstractmethod
    def query_by_lemma_meaning_root_vowels(
        self,
        word: Optional[CollatedFieldQuery],
        meaning: Optional[CollatedFieldQuery],
        root: Optional[CollatedFieldQuery],
        vowel_class: Optional[CollatedFieldQuery],
    ) -> Sequence: ...

    @abstractmethod
    def query_by_lemma_prefix(self, query: str) -> Sequence: ...

    @abstractmethod
    def list_all_words(self) -> Sequence: ...

    @abstractmethod
    def update(self, word) -> None: ...
