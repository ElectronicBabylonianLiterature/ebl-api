import re
import unicodedata
from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, Sequence, Tuple, Union

import attr

from ebl.text.atf import ATF_SPEC, UNIDENTIFIED_SIGN, VARIANT_SEPARATOR

EMPTY_PATTERN = '^$'
UNCLEAR_PATTERN = ATF_SPEC['unclear']
WITH_SIGN_PATTERN = ATF_SPEC['with_sign']
NUMBER_PATTERN = ATF_SPEC['number']
GRAPHEME_PATTERN = ATF_SPEC['grapheme']
READING_PATTERN = ATF_SPEC['reading']
VARIANT_PATTERN = ATF_SPEC['variant']
INVALID_READING = '?'


def unicode_to_int(string):
    return int(unicodedata.normalize('NFKC', string))


def get_group(group):
    return lambda match: match.group(group)


ReadingKey = Tuple[str, Optional[int]]
SignMap = Mapping[ReadingKey, str]


@attr.s(frozen=True)
class Value(ABC):
    @abstractmethod
    def to_sign(self, sign_map: SignMap) -> str:
        ...

    @property
    def keys(self) -> Sequence[ReadingKey]:
        return []


@attr.s(auto_attribs=True, frozen=True)
class Reading(Value):
    reading: str
    sub_index: Optional[int]
    default: str

    @property
    def key(self):
        return self.reading, self.sub_index

    @property
    def keys(self) -> Sequence[ReadingKey]:
        return [self.key]

    def to_sign(self, sign_map: SignMap) -> str:
        return sign_map.get(self.key, self.default)


@attr.s(auto_attribs=True, frozen=True)
class NotReading(Value):
    value: str

    def to_sign(self, _) -> str:
        return self.value


@attr.s(auto_attribs=True, frozen=True)
class Variant(Value):
    values: Tuple[Union[Reading, NotReading], ...]

    @property
    def keys(self) -> Sequence[ReadingKey]:
        return [key for value in self.values for key in value.keys]

    def to_sign(self, sign_map: SignMap) -> str:
        return VARIANT_SEPARATOR.join([
            value.to_sign(sign_map)
            for value
            in self.values
        ])


def map_cleaned_reading(cleaned_reading: str) -> Union[
    Value, List[Value]
]:
    def map_(value):
        factories = [
            (EMPTY_PATTERN, lambda _: NotReading('')),
            (UNCLEAR_PATTERN, lambda _: NotReading(UNIDENTIFIED_SIGN)),
            (WITH_SIGN_PATTERN, lambda match: NotReading(match.group(1))),
            (NUMBER_PATTERN, map_number),
            (GRAPHEME_PATTERN, lambda match: NotReading(match.group(0))),
            (READING_PATTERN, map_reading),
            (VARIANT_PATTERN, map_variant)
        ]

        return next((
            factory(match)
            for match, factory in [
                (re.fullmatch(pattern, value), factory)
                for pattern, factory in factories
            ]
            if match
        ), NotReading(INVALID_READING))

    def map_number(match):
        value = match.group(0)
        return Reading(value, 1, value)

    def map_reading(match):
        sub_index = (
            unicode_to_int(match.group(2))
            if match.group(2)
            else 1
        )
        return Reading(match.group(1), sub_index, INVALID_READING)

    def map_variant(match):
        return Variant(tuple(
            map_(part)
            for part
            in match.group(0).split(VARIANT_SEPARATOR)
        ))

    return map_(cleaned_reading)
