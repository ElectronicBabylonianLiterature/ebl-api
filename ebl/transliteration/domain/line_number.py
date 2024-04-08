from abc import ABC, abstractmethod
from typing import Optional
from ebl.bibliography.domain.reference import Reference

import attr


class AbstractLineNumber(ABC):
    @property
    @abstractmethod
    def label(self) -> str: ...

    @property
    @abstractmethod
    def is_beginning_of_side(self) -> bool: ...

    @property
    def atf(self) -> str:
        return f"{self.label}."

    @abstractmethod
    def is_matching_number(self, number: int) -> bool: ...


@attr.s(auto_attribs=True, frozen=True)
class LineNumber(AbstractLineNumber):
    number: int
    has_prime: bool = False
    prefix_modifier: Optional[str] = None
    suffix_modifier: Optional[str] = None

    @property
    def label(self) -> str:
        prefix = f"{self.prefix_modifier}+" if self.prefix_modifier else ""
        prime = "'" if self.has_prime else ""
        suffix = self.suffix_modifier or ""
        return f"{prefix}{self.number}{prime}{suffix}"

    @property
    def is_beginning_of_side(self) -> bool:
        return self.number == 1 and not self.has_prime and self.prefix_modifier is None

    def is_matching_number(self, number: int) -> bool:
        return number == self.number


@attr.s(auto_attribs=True, frozen=True)
class LineNumberRange(AbstractLineNumber):
    start: LineNumber
    end: LineNumber

    @property
    def label(self) -> str:
        return f"{self.start.label}-{self.end.label}"

    @property
    def is_beginning_of_side(self) -> bool:
        return self.start.is_beginning_of_side

    def is_matching_number(self, number: int) -> bool:
        return self.start.number <= number <= self.end.number


@attr.s(auto_attribs=True, frozen=True)
class OldLineNumber:
    number: str
    reference: Reference
