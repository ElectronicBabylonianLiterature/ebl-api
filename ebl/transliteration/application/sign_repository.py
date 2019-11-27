from abc import ABC, abstractmethod
from typing import List, Optional

from ebl.transliteration.domain.sign import Sign, SignName
from ebl.transliteration.domain.sign_map import SignKey


class SignRepository(ABC):
    @abstractmethod
    def create(self, sign: Sign) -> str:
        ...

    @abstractmethod
    def find(self, name: SignName) -> Sign:
        ...

    @abstractmethod
    def search(self, reading, sub_index) -> Optional[Sign]:
        ...

    @abstractmethod
    def search_many(self, readings: List[SignKey]) -> List[Sign]:
        ...
