from abc import ABC, abstractmethod
from typing import Optional, Sequence

from ebl.transliteration.domain.sign import Sign, SignName


class SignRepository(ABC):
    @abstractmethod
    def create(self, sign: Sign) -> str:
        ...

    @abstractmethod
    def find(self, name: SignName) -> Sign:
        ...

    @abstractmethod
    def search_by_id(self, query: str) -> Sequence[Sign]:
        ...

    @abstractmethod
    def search_all(self, reading: str, sub_index: Optional[str] = None) -> Sequence[Sign]:
        ...

    @abstractmethod
    def search_composite_signs(self, reading, sub_index) -> Sequence[Sign]:
        ...

    @abstractmethod
    def search(self, reading, sub_index) -> Optional[Sign]:
        ...
