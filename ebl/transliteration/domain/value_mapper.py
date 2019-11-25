import re

from ebl.transliteration.domain.atf import ATF_SPEC, UNCLEAR_SIGN, \
    UNIDENTIFIED_SIGN, \
    VARIANT_SEPARATOR, sub_index_to_int
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.standardization import is_splittable
from ebl.transliteration.domain.value import Value, ValueFactory

EMPTY_PATTERN = '^$'
UNCLEAR_PATTERN = UNCLEAR_SIGN
UNIDENTIFIED_PATTER = UNIDENTIFIED_SIGN
WITH_SIGN_PATTERN = ATF_SPEC['with_sign']
NUMBER_PATTERN = ATF_SPEC['number']
GRAPHEME_PATTERN = ATF_SPEC['grapheme']
READING_PATTERN = ATF_SPEC['reading']
VARIANT_PATTERN = ATF_SPEC['variant']


def get_group(group):
    return lambda match: match.group(group)


def map_number(match):
    value = match.group(0)
    return ValueFactory.create_number(value)


def map_reading(match):
    sub_index = (
        sub_index_to_int(match.group(2))
        if match.group(2)
        else 1
    )
    return ValueFactory.create_reading(match.group(1), sub_index)


def map_variant(match):
    return ValueFactory.create_variant(tuple(
        parse_reading(part, True)
        for part
        in match.group(0).split(VARIANT_SEPARATOR)
    ))


def map_splittable_grapheme_from_group(index: int):
    def map_(match):
        name = SignName(match.group(index))
        return (
            ValueFactory.create_splittable_grapheme(name)
            if is_splittable(name)
            else ValueFactory.create_grapheme(name)
        )

    return map_


def map_grapheme_from_group(index: int):
    def map_(match):
        name = SignName(match.group(index))
        return ValueFactory.create_grapheme(name)

    return map_


def parse_reading(cleaned_reading: str, is_in_variant=False) -> Value:
    factories = [
        (EMPTY_PATTERN, lambda _: ValueFactory.EMPTY),
        (UNCLEAR_PATTERN, lambda _: ValueFactory.UNIDENTIFIED),
        (UNIDENTIFIED_PATTER, lambda _: ValueFactory.UNIDENTIFIED),
        (WITH_SIGN_PATTERN, map_splittable_grapheme_from_group(1)),
        (NUMBER_PATTERN, map_number),
        (GRAPHEME_PATTERN, (map_grapheme_from_group(0)
                            if is_in_variant
                            else map_splittable_grapheme_from_group(0))),
        (READING_PATTERN, map_reading),
        (VARIANT_PATTERN, map_variant)
    ]

    return next((
        factory(match)
        for match, factory in [
            (re.fullmatch(pattern, cleaned_reading), factory)
            for pattern, factory in factories
        ]
        if match
    ), ValueFactory.INVALID)
