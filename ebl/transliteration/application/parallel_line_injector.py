from abc import ABC, abstractmethod
from typing import Sequence, TypeVar

from ebl.transliteration.domain.line import Line


T = TypeVar("T", bound=Line)


class ParallelLineInjector(ABC):
    @abstractmethod
    def inject(self, lines: Sequence[T]) -> Sequence[T]:
        ...
