import re
import unicodedata


BROKEN_PATTERN = r'x'
WITH_SIGN_PATTERN = r'[^\(/\|]+\((.+)\)|'
NUMBER_PATTERN = r'\d+'
GRAPHEME_PATTERN =\
    r'\|?(\d*[.x×%&+@]?\(?[A-ZṢŠṬ₀-₉]+([@~][a-z0-9]+)*\)?)+\|?'
READING_PATTERN = r'([^₀-₉ₓ/]+)([₀-₉ₓ]+)?'
VARIANT_PATTERN = r'([^/]+)(?:/([^/]+))+'
UNKNOWN_SIGN = '?'
BROKEN_SIGN = 'X'


def unicode_to_int(string):
    return int(unicodedata.normalize('NFKC', string))


class ValueMapper:

    def __init__(self, sign_repository):
        self._repository = sign_repository

    def map(self, value):
        factories = [
            (BROKEN_PATTERN, lambda _: BROKEN_SIGN),
            (WITH_SIGN_PATTERN, lambda match: match.group(1)),
            (NUMBER_PATTERN, self._map_number),
            (GRAPHEME_PATTERN, lambda match: match.group(0)),
            (READING_PATTERN, self._map_reading),
            (VARIANT_PATTERN, self._map_variant)
        ]

        return next((
            factory(match)
            for match, factory in [
                (re.fullmatch(pattern, value), factory)
                for pattern, factory in factories
            ]
            if match
        ), UNKNOWN_SIGN)

    def _map_number(self, match):
        value = match.group(0)
        return self._search_or_default(value, 1, value)

    def _map_reading(self, match):
        value = match.group(1)
        sub_index = (
            unicode_to_int(match.group(2))
            if match.group(2)
            else 1
        )
        return self._search_or_default(value, sub_index, UNKNOWN_SIGN)

    def _map_variant(self, match):
        return '/'.join([
            self.map(part)
            for part
            in match.group(0).split('/')
        ])

    def _search_or_default(self, value, sub_index, default):
        sign = self._repository.search(value, sub_index)
        return sign['_id'] if sign else default
