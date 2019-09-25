from typing import List, Sequence, Tuple

import pydash

from ebl.atf.atf import Atf
from ebl.transliteration_search.application.sign_repository import \
    SignRepository
from ebl.transliteration_search.domain.clean_atf import CleanAtf
from ebl.transliteration_search.domain.sign import Sign
from ebl.transliteration_search.domain.sign_map import SignKey, SignMap
from ebl.transliteration_search.domain.standardization import Standardization
from ebl.transliteration_search.domain.value import Value
from ebl.transliteration_search.domain.value_mapper import parse_reading

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

    def convert_atf_to_signs(self, atf: Atf) -> str:
        values = CleanAtf(atf).values
        return '\n'.join([
            ' '.join(row)
            for row in self.convert_values_to_signs(values)
        ])

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
