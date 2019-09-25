from typing import List, Sequence, Tuple

import pydash

from ebl.atf.domain.atf import Atf
from ebl.atf.domain.clean_atf import CleanAtf
from ebl.signs.application.sign_repository import SignRepository
from ebl.signs.domain.sign import Sign
from ebl.signs.domain.sign_map import SignKey, SignMap
from ebl.signs.domain.standardization import Standardization
from ebl.signs.domain.value import Value
from ebl.signs.domain.value_mapper import parse_reading

SignMapEntry = Tuple[SignKey, Standardization]


def sign_to_pair(sign: Sign) -> Sequence[SignMapEntry]:
    standardization = Standardization.of_sign(sign)
    mapping: List[SignMapEntry] = [
        (value, standardization)
        for value in sign.values
    ]
    mapping.append((sign.name, standardization))
    return mapping


class AtfConverter:

    def __init__(self, sign_repository: SignRepository):
        self._sign_repository = sign_repository

    def convert_atf_to_sign_matrix(self, atf: Atf) -> Sequence[Sequence[str]]:
        values = self.convert_atf_to_values(atf)
        return self.convert_values_to_signs(values)

    def convert_atf_to_values(self, atf: Atf) -> Sequence[Sequence[Value]]:
        return (
            pydash
            .chain(CleanAtf(atf).cleaned)
            .map(lambda row: [
                parse_reading(value)
                for value in row
            ])
            .value()
        )

    def convert_values_to_signs(
        self, values: Sequence[Sequence[Value]]
    ) -> Sequence[Sequence[str]]:
        sign_map = self._create_sign_map(values)
        return [
            [
                reading_part
                for reading in row
                for reading_part in reading.to_sign(sign_map, True).split(' ')

            ]
            for row in values
        ]

    def _create_sign_map(
            self, values: Sequence[Sequence[Value]]
    ) -> SignMap:
        sign_map: SignMap = (
            pydash
            .chain(values)
            .flatten()
            .flat_map(lambda value: value.keys)
            .thru(self._sign_repository.search_many)
            .flat_map(sign_to_pair)
            .map_(lambda pair: self._expand_splittable(pair))
            .from_pairs()
            .value()
        )
        return sign_map

    def _expand_splittable(self, pair: SignMapEntry) -> SignMapEntry:
        key, standardization = pair

        if standardization.is_splittable:
            value = parse_reading(standardization.deep)
            sign_map = self._create_sign_map([[value]])
            return key, Standardization(value.to_sign(sign_map, True),
                                        standardization.shallow)
        else:
            return pair
