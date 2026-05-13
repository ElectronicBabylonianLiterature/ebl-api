from abc import ABC, abstractmethod
from typing import Sequence

from ebl.realia.domain.realia_entry import RealiaEntry


class RealiaRepository(ABC):
    @abstractmethod
    def find(self, realia_id: str) -> RealiaEntry:
        raise NotImplementedError()

    @abstractmethod
    def search(self, query: str) -> Sequence[RealiaEntry]:
        raise NotImplementedError()
