from abc import ABC, abstractmethod
from typing import Sequence, Optional
from ebl.common.query.query_collation import CollatedFieldQuery

from ebl.dictionary.domain.word import WordId


class WordRepository(ABC):
    @abstractmethod
    def create(self, word) -> WordId:
        raise NotImplementedError

    @abstractmethod
    def create_proper_noun(self, lemma: str, named_entity_tags: list[str]) -> WordId:
        raise NotImplementedError

    @abstractmethod
    def query_by_id(self, id_: WordId):
        raise NotImplementedError

    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence:
        raise NotImplementedError

    @abstractmethod
    def query_by_lemma_meaning_root_vowels(
        self,
        word: Optional[CollatedFieldQuery],
        meaning: Optional[CollatedFieldQuery],
        root: Optional[CollatedFieldQuery],
        vowel_class: Optional[list[tuple[str, ...]]],
        origin: Optional[list[str]] = None,
    ) -> Sequence:
        raise NotImplementedError

    @abstractmethod
    def query_by_lemma_prefix(self, query: str) -> Sequence:
        raise NotImplementedError

    @abstractmethod
    def list_all_words(self) -> Sequence:
        raise NotImplementedError

    @abstractmethod
    def update(self, word) -> None:
        raise NotImplementedError
