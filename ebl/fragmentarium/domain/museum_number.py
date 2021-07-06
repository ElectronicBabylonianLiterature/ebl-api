import functools
import re
from typing import Mapping

import attr


def _is_not_empty(_, attribute: attr.Attribute, value: str) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute} cannot be an empty string.")


def _does_not_contain_period(_, attribute: attr.Attribute, value: str) -> None:
    if "." in value:
        raise ValueError(f"Attribute {attribute} cannot contain '.'.")


def _require_suffix_if_contains_period(
    museum_number: "MuseumNumber", attribute: attr.Attribute, value: str
) -> None:
    if "." in value and not museum_number.suffix:
        raise ValueError("If {attribute} contains period suffix cannot be empty.")


PREFIX_ORER: Mapping[str, int] = {
    "K": 1,
    "Sm": 2,
    "DT": 3,
    "Rm": 4,
    "Rm-II": 5,
    "BM": 7,
    "CBS": 8,
    "UM": 9,
    "N": 10,
}
NUMBER_PREFIX_ORDER: int = 6
DEFAULT_PREFIX_ORDER: int = 11


@functools.total_ordering
@attr.s(auto_attribs=True, frozen=True, order=False)
class MuseumNumber:
    prefix: str = attr.ib(validator=[_is_not_empty, _require_suffix_if_contains_period])
    number: str = attr.ib(validator=[_is_not_empty, _does_not_contain_period])
    suffix: str = attr.ib(default="", validator=_does_not_contain_period)

    def __lt__(self, other):
        if not isinstance(other, MuseumNumber):
            return NotImplemented
        return (self.prefix_order, self.prefix, self.number, self.suffix) < (
            other.prefix_order,
            other.prefix,
            other.number,
            other.suffix,
        )

    def __str__(self) -> str:
        if self.suffix:
            return f"{self.prefix}.{self.number}.{self.suffix}"
        else:
            return f"{self.prefix}.{self.number}"

    @property
    def prefix_order(self) -> int:
        return (
            NUMBER_PREFIX_ORDER
            if self.prefix.isnumeric()
            else PREFIX_ORER.get(self.prefix, DEFAULT_PREFIX_ORDER)
        )

    @staticmethod
    def of(source: str) -> "MuseumNumber":
        pattern = re.compile(r"(.+?)\.([^.]+)(?:\.([^.]+))?")
        match = pattern.fullmatch(source)
        if match:
            return MuseumNumber(match.group(1), match.group(2), match.group(3) or "")
        else:
            raise ValueError(f"'{source}' is not a valid museum number.")
