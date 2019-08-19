import pydash
from ebl.sign_list.value_mapper import map_cleaned_reading, VARIANT_SEPARATOR
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
            (
                [
                    map_cleaned_reading(value)
                    for value in row.split(ATF_SPEC['word_separator'])
                ]
                if row
                else ['']
            )
            for row in cleaned_transliteration
        ]

        def map_sign(sign):
            return [
                [(value['value'], value.get('subIndex')), sign['_id']]
                for value in sign['values']
            ]

        sign_map = (
            pydash
            .chain(values)
            .flatten_deep()
            .reject(pydash.is_string)
            .map(lambda reading: reading.key)
            .thru(self._repository.search_many)
            .flat_map(map_sign)
            .from_pairs()
            .value()
        )

        return [
            [
                reading
                if pydash.is_string(reading)
                else (
                    VARIANT_SEPARATOR.join([
                        sign_map.get(variant.key, variant.default)
                        for variant
                        in reading
                    ])
                    if pydash.is_list(reading)
                    else sign_map.get(reading.key, reading.default)
                )
                for reading in row
            ]
            for row in values
        ]
