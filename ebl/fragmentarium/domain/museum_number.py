import functools
import math
import operator
import re
from typing import Mapping, Tuple, Union, Dict, TypedDict

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
    "CBS": 8,
    "UM": 9,
    "N": 10,
}
NUMBER_PREFIX_ORDER: int = 6
DEFAULT_PREFIX_ORDER: int = 11

def prefix_order(prefix: str) -> Tuple[int, int, str]:
   return NUMBER_PREFIX_ORDER if prefix.isnumeric() else PREFIX_ORDER.get(prefix, DEFAULT_PREFIX_ORDER), int(prefix) if prefix.isnumeric() else 0, prefix

def number_order(number: str) -> Tuple[float, str]:
    return int(number) if number.isnumeric() else math.inf, number


def suffix_order(suffix: str) -> Tuple[float, str]:
    return int(suffix) if suffix.isnumeric() else math.inf, suffix

def convert_to_order_number(prefix: str,number: str, suffix:str) -> Tuple[int, int, str]:
    prefix_order_number = prefix_order(prefix)
    number_order_number = number_order(number)
    suffix_order_number = suffix_order(suffix)
    return (*prefix_order_number, *number_order_number, *suffix_order_number)

class MuseumNumberDict(TypedDict):
    prefix: str
    number: str
    suffix: str

def compare_museum_number(first: MuseumNumberDict, second: MuseumNumberDict, comparator = operator.lt)->bool:
    return comparator(convert_to_order_number(**first), convert_to_order_number(**second))





@functools.total_ordering
@attr.s(auto_attribs=True, frozen=True, order=False)
class MuseumNumber:
    prefix: str = attr.ib(validator=[_is_not_empty, _require_suffix_if_contains_period])
    number: str = attr.ib(validator=[_is_not_empty, _does_not_contain_period])
    suffix: str = attr.ib(default="", validator=_does_not_contain_period)

    def __lt__(self, other):
        return (
            convert_to_order_number(self.prefix, self.number, self.suffix)
            <  convert_to_order_number(other.prefix, other.number, other.suffix)
            if isinstance(other, MuseumNumber)
            else NotImplemented
        )

    def __str__(self) -> str:
        if self.suffix:
            return f"{self.prefix}.{self.number}.{self.suffix}"
        else:
            return f"{self.prefix}.{self.number}"

    @staticmethod
    def of(source: str) -> "MuseumNumber":
        match = re.compile(r"(.+?)\.([^.]+)(?:\.([^.]+))?").fullmatch(source)
        if match:
            return MuseumNumber(match.group(1), match.group(2), match.group(3) or "")
        else:
            raise ValueError(f"'{source}' is not a valid museum number.")
