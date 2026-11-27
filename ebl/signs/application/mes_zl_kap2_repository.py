from abc import ABC, abstractmethod
from typing import Sequence

from ebl.signs.domain.mes_zl_kap2 import MesZlKap2Entry


class MesZlKap2Repository(ABC):
    @abstractmethod
    def find_by_numbers(self, numbers: Sequence[str]) -> Sequence[MesZlKap2Entry]:
        raise NotImplementedError()
