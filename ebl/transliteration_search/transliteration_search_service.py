from typing import Sequence

import pydash

from ebl.text.atf import Atf
from ebl.transliteration_search.clean_atf import CleanAtf
from ebl.transliteration_search.value import SignMap, Value


class TransliterationSearch:

    def __init__(self, sign_repository):
        self._repository = sign_repository

    def convert_atf_to_signs(self, atf: Atf) -> str:
        values = CleanAtf(atf).values
        return '\n'.join([
            ' '.join(row)
            for row in self.convert_values_to_signs(values)
        ])

    def convert_values_to_signs(
        self, values: Sequence[Sequence[Value]]
    ) -> Sequence[Sequence[str]]:
        def sign_to_pair(sign):
            standardization = (sign.standardization
                               .replace('/', '\\u002F')
                               .replace(' ', '\\u0020'))
            mapping = [
                [(value.value, value.sub_index), standardization]
                for value in sign.values
            ]
            mapping.append([sign.name, standardization])
            return mapping

        sign_map: SignMap = (
            pydash
            .chain(values)
            .flatten()
            .flat_map(lambda reading: reading.keys)
            .thru(self._repository.search_many)
            .flat_map(sign_to_pair)
            .from_pairs()
            .value()
        )

        return [
            [
                reading_part
                for reading in row
                for reading_part in reading.to_sign(sign_map).split(' ')

            ]
            for row in values
        ]
