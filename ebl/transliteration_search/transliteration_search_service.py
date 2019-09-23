from typing import List, Sequence, Tuple

import pydash

from ebl.atf.atf import Atf
from ebl.atf.clean_atf import CleanAtf
from ebl.fragment.fragment_info import FragmentInfo
from ebl.sign_list.sign import Sign
from ebl.transliteration_search.transliteration_query import \
    TransliterationQuery
from ebl.transliteration_search.value import AnyKey, SignMap, Value
from ebl.transliteration_search.value_mapper import is_splittable, \
    parse_reading

SignMapEntry = Tuple[AnyKey, str]


def escape_standardization(sign) -> str:
    return (sign.standardization
            .replace('/', '\\u002F')
            .replace(' ', '\\u0020'))


def sign_to_pair(sign: Sign) -> Sequence[SignMapEntry]:
    standardization = (sign.name
                       if is_splittable(sign.name)
                       else escape_standardization(sign))
    mapping: List[SignMapEntry] = [
        ((value.value, value.sub_index), standardization)
        for value in sign.values
    ]
    mapping.append((sign.name, standardization))
    return mapping


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
        sign_map = self._create_sign_map(values)
        return [
            [
                reading_part
                for reading in row
                for reading_part in reading.to_sign(sign_map).split(' ')

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

    def _expand_splittable(self,
                           pair: SignMapEntry) -> SignMapEntry:
        key, standardization = pair

        if is_splittable(standardization):
            value = parse_reading(standardization)
            sign_map = self._create_sign_map([[value]])
            return key, value.to_sign(sign_map)
        else:
            return pair

    def search(self, query: TransliterationQuery) -> List[FragmentInfo]:
        return [
            FragmentInfo.of(fragment, query.get_matching_lines(fragment))
            for fragment
            in self._fragment_repository.search_signs(query)
        ]
