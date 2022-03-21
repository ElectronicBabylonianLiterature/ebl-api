from abc import ABC, abstractmethod
from typing import Sequence


class ParalallelLineInjector(ABC):
    @abstractmethod
    def inject_exists(
        self,
        lines: Sequence[dict],
    ) -> Sequence[dict]:
        ...
