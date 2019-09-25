from abc import ABC, abstractmethod
from typing import Optional, Sequence, Tuple

import attr

from ebl.atf.domain.atf import UNIDENTIFIED_SIGN, VARIANT_SEPARATOR
from ebl.signs.domain.sign import SignName, Value as SignValue
from ebl.signs.domain.sign_map import SignKey, SignMap
from ebl.signs.domain.standardization import Standardization

INVALID_READING = '?'


@attr.s(frozen=True)
class Value(ABC):

    @abstractmethod
    def to_sign(self, sign_map: SignMap, is_deep: bool) -> str:
        ...

    @property
    def keys(self) -> Sequence[SignKey]:
        return []


@attr.s(auto_attribs=True, frozen=True)
class Reading(Value):
    reading: str
    sub_index: Optional[int]
    default: str

    @property
    def key(self) -> SignValue:
        return SignValue(self.reading, self.sub_index)

    @property
    def keys(self) -> Sequence[SignValue]:
        return [self.key]

    def to_sign(self, sign_map: SignMap, is_deep) -> str:
        return sign_map.get(
            self.key, Standardization.of_string(self.default)
        ).get_value(is_deep)


@attr.s(auto_attribs=True, frozen=True)
class NotReading(Value):
    value: str

    def to_sign(self, _sign_map, _is_deep) -> str:
        return self.value


@attr.s(auto_attribs=True, frozen=True)
class Grapheme(Value):
    name: SignName

    @property
    def key(self) -> SignName:
        return self.name

    @property
    def keys(self) -> Sequence[SignName]:
        return [self.key]

    def to_sign(self, sign_map: SignMap, is_deep) -> str:
        return sign_map.get(
            self.key, Standardization.of_string(self.name)
        ).get_value(is_deep)


@attr.s(auto_attribs=True, frozen=True)
class SplittableGrapheme(Value):
    values: Tuple[Grapheme, ...] = attr.ib()

    @classmethod
    def of(cls, names: Sequence[SignName]):
        return SplittableGrapheme(tuple(map(Grapheme, names)))

    @values.validator
    def _check_values(self, _attribute, value):
        if any(type(entry) != Grapheme for entry in value):
            raise ValueError('SplittableGrapheme can only contain Graphemes.')

    @property
    def keys(self) -> Sequence[SignKey]:
        return [key for value in self.values for key in value.keys]

    def to_sign(self, sign_map: SignMap, is_deep) -> str:
        return ' '.join([
            value.to_sign(sign_map, is_deep)
            for value
            in self.values
        ])


@attr.s(auto_attribs=True, frozen=True)
class Variant(Value):
    values: Tuple[Value, ...] = attr.ib()

    @values.validator
    def _check_values(self, _attribute, value):
        if any(type(entry) == Variant for entry in value):
            raise ValueError('Variants cannot be nested.')
        if any(type(entry) == SplittableGrapheme for entry in value):
            raise ValueError('Variants cannot contain SplittableGraphemes.')

    @property
    def keys(self) -> Sequence[SignKey]:
        return [key for value in self.values for key in value.keys]

    def to_sign(self, sign_map: SignMap, _) -> str:
        return VARIANT_SEPARATOR.join([
            value.to_sign(sign_map, False)
            for value
            in self.values
        ])


class ValueFactory:
    EMPTY = NotReading('')
    UNIDENTIFIED = NotReading(UNIDENTIFIED_SIGN)
    INVALID = NotReading(INVALID_READING)

    @staticmethod
    def create_reading(value: str, sub_index: Optional[int]) -> Reading:
        return Reading(value, sub_index, INVALID_READING)

    @staticmethod
    def create_number(value: str) -> Reading:
        return Reading(value, 1, value)

    @staticmethod
    def create_variant(values: Tuple[Value, ...]) -> Variant:
        return Variant(values)

    @staticmethod
    def create_grapheme(value: SignName) -> Grapheme:
        return Grapheme(value)

    @staticmethod
    def create_splittable_grapheme(value: str) -> SplittableGrapheme:
        graphemes = value.strip('|').split('.')
        return SplittableGrapheme.of([SignName(name) for name in graphemes])
