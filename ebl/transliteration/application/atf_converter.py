from typing import List, Sequence, Tuple
from itertools import chain

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.clean_atf import CleanAtf
from ebl.transliteration.domain.sign import Sign
from ebl.transliteration.domain.sign_map import SignKey, SignMap
from ebl.transliteration.domain.standardization import Standardization
from ebl.transliteration.domain.value import Value
from ebl.transliteration.domain.value_mapper import parse_reading

SignMapEntry = Tuple[SignKey, Standardization]


def sign_to_pair(sign: Sign) -> Sequence[SignMapEntry]:
    standardization = Standardization.of_sign(sign)
    mapping: List[SignMapEntry] = [(value, standardization) for value in sign.values]
    mapping.append((sign.name, standardization))
    return mapping


class AtfConverter:
    def __init__(self, sign_repository: SignRepository):
        self._sign_repository = sign_repository

    def convert_atf_to_sign_matrix(self, atf: Atf) -> Sequence[Sequence[str]]:
        values = self.convert_atf_to_values(atf)
        return self.convert_values_to_signs(values)

    def convert_atf_to_values(self, atf: Atf) -> Sequence[Sequence[Value]]:
        return list(map(lambda row: [parse_reading(value)
                                     for value in row], CleanAtf(atf).cleaned))

    def convert_values_to_signs(
        self, values: Sequence[Sequence[Value]]
    ) -> Sequence[Sequence[str]]:
        sign_map = self._create_sign_map(values)
        return [
            [
                reading_part
                for reading in row
                for reading_part in reading.to_sign(sign_map, True).split(" ")
            ]
            for row in values
        ]

    def _create_sign_map(self, values: Sequence[Sequence[Value]]) -> SignMap:
        sign_map = [key for value in chain.from_iterable(values) for key in value.keys]
        sign_map = self._sign_repository.search_many(sign_map)
        sign_map = [inner for entry in map(sign_to_pair, sign_map) for inner in entry]
        sign_map = {key: value for key, value in map(self._expand_splittable, sign_map)}
        return sign_map

    def _expand_splittable(self, pair: SignMapEntry) -> SignMapEntry:
        key, standardization = pair

        if standardization.is_splittable:
            value = parse_reading(standardization.deep)
            sign_map = self._create_sign_map([[value]])
            return (
                key,
                Standardization(value.to_sign(sign_map, True), standardization.shallow),
            )
        else:
            return pair
