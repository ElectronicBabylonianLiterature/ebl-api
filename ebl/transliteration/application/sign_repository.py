from abc import ABC, abstractmethod
from typing import Optional

from ebl.transliteration.domain.sign import Sign, SignName


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
