from typing import List, Sequence

import pydash

from ebl.atf.atf import Atf
from ebl.atf.clean_atf import CleanAtf
from ebl.fragment.fragment_info import FragmentInfo
from ebl.transliteration_search.transliteration_query import \
    TransliterationQuery
from ebl.transliteration_search.value import SignMap, Value


class TransliterationSearch:

    def __init__(self, sign_repository, fragment_repository):
        self._sign_repository = sign_repository
        self._fragment_repository = fragment_repository

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
            .thru(self._sign_repository.search_many)
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

    def search(self, query: TransliterationQuery) -> List[FragmentInfo]:
        return [
            FragmentInfo.of(fragment, query.get_matching_lines(fragment))
            for fragment
            in self._fragment_repository.search_signs(query)
        ]
