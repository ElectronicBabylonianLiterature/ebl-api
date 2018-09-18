import re
import unicodedata

from ebl.mongo_repository import MongoRepository


COLLECTION = 'signs'
UNKNOWN_SIGN = 'X'


class MongoSignList(MongoRepository):

    def __init__(self, database):
        super().__init__(database, COLLECTION)

    def search(self, reading, sub_index):
        sub_index_query =\
            {'$exists': False} if sub_index is None else sub_index
        return self.get_collection().find_one({
            'values': {
                '$elemMatch': {
                    'value': reading,
                    'subIndex': sub_index_query
                }
            }
        })

    def map_transliteration(self, cleaned_transliteration):
        return [self._parse_row(row) for row in cleaned_transliteration]

    def _parse_row(self, row):
        return [self._parse_value(value) for value in row.split(' ')]

    def _parse_value(self, value):
        match = re.fullmatch(r'\|?(\d*[.x×%&+]?[A-ZṢŠṬ₀-₉]+)+\|?|'
                             r'\d+|'
                             r'[^\(]+\((.+)\)', value)
        if match:
            return match.group(2) or value
        else:
            return self._parse_reading(value)

    def _parse_reading(self, reading):
        reading_match = re.fullmatch(r'([^₀-₉ₓ/]+)([₀-₉ₓ]+)?', reading)
        variant_match = re.search(r'/', reading)
        if reading_match:
            return self._parse_match(reading_match)
        elif variant_match:
            return self._parse_variant(reading)
        else:
            return UNKNOWN_SIGN

    def _parse_match(self, match):
        value = match.group(1)
        sub_index = match.group(2) or '1'
        normalized_sub_index = unicodedata.normalize('NFKC', sub_index)
        sign = self.search(value, int(normalized_sub_index))
        return sign['_id'] if sign else UNKNOWN_SIGN

    def _parse_variant(self, reading):
        return '/'.join([
            self._parse_reading(part)
            for part
            in reading.split('/')
        ])
