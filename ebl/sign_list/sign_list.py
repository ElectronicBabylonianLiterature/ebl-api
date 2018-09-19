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
        return [
            [self._parse_value(value) for value in row.split(' ')]  
            for row in cleaned_transliteration
        ]

    def _parse_value(self, value):
        grapheme_match = re.fullmatch(
            r'\|?(\d*[.x×%&+@]?[A-ZṢŠṬ₀-₉]+)+\|?|'
                             r'\d+|'
            r'[^\(]+\((.+)\)', value
        )
        reading_match = re.fullmatch(r'([^₀-₉ₓ/]+)([₀-₉ₓ]+)?', value)
        if grapheme_match:
            return self._parse_grapheme(grapheme_match)
        elif reading_match:
            return self._parse_reading(reading_match)
        elif '/' in value:
            return self._parse_variant(value)
        else:
            return UNKNOWN_SIGN

    def _parse_grapheme(self, match):
        return match.group(2) or match.group(0)

    def _parse_reading(self, match):
        value = match.group(1)
        sub_index = (
            int(unicodedata.normalize('NFKC', match.group(2)))
            if match.group(2)
            else 1
        )
        sign = self.search(value, sub_index)
        return sign['_id'] if sign else UNKNOWN_SIGN

    def _parse_variant(self, reading):
        return '/'.join([
            self._parse_value(part)
            for part
            in reading.split('/')
        ])
