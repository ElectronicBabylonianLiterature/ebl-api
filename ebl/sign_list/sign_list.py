import re
import unicodedata


UNKNOWN_SIGN = 'X'


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
