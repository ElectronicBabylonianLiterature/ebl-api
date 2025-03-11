import functools
import math
import re
from typing import Mapping, Tuple

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
        raise ValueError(f"If {attribute} contains period suffix cannot be empty.")


PREFIX_ORDER: Mapping[str, int] = {
    "K": 1,
    "Sm": 2,
    "DT": 3,
    "Rm": 4,
    "Rm-II": 5,
    "BM": 7,
    "IM": 8,
    "ISACM-A": 9,
    "CBS": 10,
    "UM": 11,
    "N": 12,
}
NUMBER_PREFIX_ORDER: int = 6
DEFAULT_PREFIX_ORDER: int = 13


@functools.total_ordering
@attr.s(auto_attribs=True, frozen=True, order=False)
class MuseumNumber:
    prefix: str = attr.ib(validator=[_is_not_empty, _require_suffix_if_contains_period])
    number: str = attr.ib(validator=[_is_not_empty, _does_not_contain_period])
    suffix: str = attr.ib(default="", validator=_does_not_contain_period)

    def __lt__(self, other):
        return (
            (*self._prefix_order, *self._number_order, *self._suffix_order)
            < (*other._prefix_order, *other._number_order, *other._suffix_order)
            if isinstance(other, MuseumNumber)
            else NotImplemented
        )

    def __str__(self) -> str:
        if self.suffix:
            return f"{self.prefix}.{self.number}.{self.suffix}"
        else:
            return f"{self.prefix}.{self.number}"

    def __eq__(self, other):
        return (
            (
                self.prefix == other.prefix
                and self.number == other.number
                and self.suffix == other.suffix
            )
            if isinstance(other, MuseumNumber)
            else NotImplemented
        )

    @property
    def _prefix_order(self) -> Tuple[int, int, str]:
        return (
            (
                NUMBER_PREFIX_ORDER
                if self.prefix.isnumeric()
                else PREFIX_ORDER.get(self.prefix, DEFAULT_PREFIX_ORDER)
            ),
            int(self.prefix) if self.prefix.isnumeric() else 0,
            self.prefix,
        )

    @property
    def _number_order(self) -> Tuple[float, str]:
        return (int(self.number) if self.number.isnumeric() else math.inf, self.number)

    @property
    def _suffix_order(self) -> Tuple[float, str]:
        return (int(self.suffix) if self.suffix.isnumeric() else math.inf, self.suffix)

    @staticmethod
    def of(source: str) -> "MuseumNumber":
        if match := re.compile(r"(.+?)\.([^.]+)(?:\.([^.]+))?").fullmatch(source):
            return MuseumNumber(match[1], match[2], match[3] or "")
        else:
            raise ValueError(f"'{source}' is not a valid museum number.")
