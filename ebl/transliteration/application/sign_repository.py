from abc import ABC, abstractmethod
from typing import Optional, Sequence

from ebl.transliteration.domain.sign import Sign, SignName


class SignRepository(ABC):
    @abstractmethod
    def create(self, sign: Sign) -> str:
        raise NotImplementedError

    @abstractmethod
    def find(self, name: SignName) -> Sign:
        raise NotImplementedError

    @abstractmethod
    def find_many(self, query, *args, **kwargs) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search_by_id(self, query: str) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search_all(self, reading: str, sub_index: int) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search_by_lists_name(self, name: str, number: str) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search_composite_signs(self, reading: str, sub_index: int) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search_include_homophones(self, reading: str) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search(self, reading: str, sub_index: Optional[int]) -> Optional[Sign]:
        raise NotImplementedError

    @abstractmethod
    def search_by_lemma(self, word_id: str) -> Sequence[Sign]:
        raise NotImplementedError

    @abstractmethod
    def list_all_signs(self) -> Sequence[str]:
        raise NotImplementedError
