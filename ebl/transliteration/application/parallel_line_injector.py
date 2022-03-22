from abc import ABC, abstractmethod
from typing import Sequence, TypeVar

from ebl.transliteration.domain.line import Line


T = TypeVar("T", bound=Line)


class ParalallelLineInjector(ABC):
    @abstractmethod
    def inject_exists(self, lines: Sequence[T]) -> Sequence[T]:
        ...
