import re
import unicodedata


BROKEN_PATTERN = r'x'
WITH_SIGN_PATTERN = r'[^\(/\|]+\((.+)\)|'
GRAPHEME_PATTERN = (
    r'\|?(\d*[.x×%&+@]?\(?[A-ZṢŠṬ₀-₉]+([@~][a-z0-9]+)*\)?)+\|?|'
    r'\d+'
)
READING_PATTERN = r'([^₀-₉ₓ/]+)([₀-₉ₓ]+)?'
VARIANT_PATTERN = r'([^/]+)(?:/([^/]+))+'
UNKNOWN_SIGN = '?'


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
        factories = [
            (BROKEN_PATTERN, lambda _match: 'X'),
            (WITH_SIGN_PATTERN, lambda match: match.group(1)),
            (GRAPHEME_PATTERN, lambda match: match.group(0)),
            (READING_PATTERN, self._parse_reading),
            (VARIANT_PATTERN, self._parse_variant)
        ]

        return next((
            factory(match)
            for match, factory in [
                (re.fullmatch(pattern, value), factory)
                for pattern, factory in factories
            ]
            if match
        ), UNKNOWN_SIGN)

    def _parse_reading(self, match):
        value = match.group(1)
        sub_index = (
            int(unicodedata.normalize('NFKC', match.group(2)))
            if match.group(2)
            else 1
        )
        sign = self.search(value, sub_index)
        return sign['_id'] if sign else UNKNOWN_SIGN

    def _parse_variant(self, match):
        return '/'.join([
            self._parse_value(part)
            for part
            in match.group(0).split('/')
        ])
