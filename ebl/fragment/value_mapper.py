import re
import unicodedata

from ebl.fragment.value import Value, ValueFactory
from ebl.text.atf import ATF_SPEC, VARIANT_SEPARATOR

EMPTY_PATTERN = '^$'
UNCLEAR_PATTERN = ATF_SPEC['unclear']
WITH_SIGN_PATTERN = ATF_SPEC['with_sign']
NUMBER_PATTERN = ATF_SPEC['number']
GRAPHEME_PATTERN = ATF_SPEC['grapheme']
READING_PATTERN = ATF_SPEC['reading']
VARIANT_PATTERN = ATF_SPEC['variant']


def unicode_to_int(string):
    return int(unicodedata.normalize('NFKC', string))


def get_group(group):
    return lambda match: match.group(group)


def parse_reading(cleaned_reading: str) -> Value:
    def map_(value):
        factories = [
            (EMPTY_PATTERN, lambda _: ValueFactory.EMPTY),
            (UNCLEAR_PATTERN, lambda _: ValueFactory.UNIDENTIFIED),
            (WITH_SIGN_PATTERN,
             lambda match: ValueFactory.create_not_reading(match.group(1))),
            (NUMBER_PATTERN, map_number),
            (GRAPHEME_PATTERN,
             lambda match: ValueFactory.create_not_reading(match.group(0))),
            (READING_PATTERN, map_reading),
            (VARIANT_PATTERN, map_variant)
        ]

        return next((
            factory(match)
            for match, factory in [
                (re.fullmatch(pattern, value), factory)
                for pattern, factory in factories
            ]
            if match
        ), ValueFactory.INVALID)

    def map_number(match):
        value = match.group(0)
        return ValueFactory.create_number(value)

    def map_reading(match):
        sub_index = (
            unicode_to_int(match.group(2))
            if match.group(2)
            else 1
        )
        return ValueFactory.create_reading(match.group(1), sub_index)

    def map_variant(match):
        return ValueFactory.create_variant(tuple(
            map_(part)
            for part
            in match.group(0).split(VARIANT_SEPARATOR)
        ))

    return map_(cleaned_reading)
