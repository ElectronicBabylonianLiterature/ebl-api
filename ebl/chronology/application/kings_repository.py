from typing import Sequence
from abc import ABC, abstractmethod

from ebl.chronology.chronology import King


class KingsRepository(ABC):
    @abstractmethod
    def list_all_kings(self, *args, **kwargs) -> Sequence[King]:
        ...
