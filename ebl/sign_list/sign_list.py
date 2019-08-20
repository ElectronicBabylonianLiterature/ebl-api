import pydash

from ebl.sign_list.value_mapper import map_cleaned_reading
from ebl.text.atf import ATF_SPEC


class SignList:

    def __init__(self, sign_repository):
        self._repository = sign_repository

    def create(self, sign):
        return self._repository.create(sign)

    def find(self, sign_name):
        return self._repository.find(sign_name)

    def search(self, reading, sub_index):
        return self._repository.search(reading, sub_index)

    def map_transliteration(self, cleaned_transliteration):
        values = [
            [
                map_cleaned_reading(value)
                for value in row.split(ATF_SPEC['word_separator'])
            ]
            for row in cleaned_transliteration
        ]

        def sign_to_pair(sign):
            return [
                [(value['value'], value.get('subIndex')), sign['_id']]
                for value in sign['values']
            ]

        sign_map = (
            pydash
            .chain(values)
            .flatten_deep()
            .flat_map(lambda reading: reading.keys)
            .thru(self._repository.search_many)
            .flat_map(sign_to_pair)
            .from_pairs()
            .value()
        )

        return [
            [
                reading.to_sign(sign_map)
                for reading in row
            ]
            for row in values
        ]
