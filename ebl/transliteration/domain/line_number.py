from abc import ABC, abstractmethod
from typing import Optional

import attr


class AbstractLineNumber(ABC):
    @property
    @abstractmethod
    def atf(self) -> str:
        ...


@attr.s(auto_attribs=True, frozen=True)
class LineNumber(AbstractLineNumber):
    number: int
    has_prime: bool = False
    prefix_modifier: Optional[str] = None
    suffix_modifier: Optional[str] = None

    @property
    def atf(self) -> str:
        prefix = f"{self.prefix_modifier}+" if self.prefix_modifier else ""
        prime = "'" if self.has_prime else ""
        suffix = self.suffix_modifier or ""
        return f"{prefix}{self.number}{prime}{suffix}."


@attr.s(auto_attribs=True, frozen=True)
class LineNumberRange(AbstractLineNumber):
    start: LineNumber
    end: LineNumber

    @property
    def atf(self) -> str:
        return f"{self.start.atf[:-1]}-{self.end.atf}"
