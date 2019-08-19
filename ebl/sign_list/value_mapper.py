import re
import unicodedata
from typing import Optional, Union, List

import attr

from ebl.text.atf import ATF_SPEC

BROKEN_PATTERN = ATF_SPEC['unclear']
WITH_SIGN_PATTERN = ATF_SPEC['with_sign']
NUMBER_PATTERN = ATF_SPEC['number']
GRAPHEME_PATTERN = ATF_SPEC['grapheme']
READING_PATTERN = ATF_SPEC['reading']
VARIANT_PATTERN = ATF_SPEC['variant']
VARIANT_SEPARATOR = ATF_SPEC['variant_separator']
UNKNOWN_SIGN = '?'
BROKEN_SIGN = 'X'


def unicode_to_int(string):
    return int(unicodedata.normalize('NFKC', string))


def get_group(group):
    return lambda match: match.group(group)


@attr.s(auto_attribs=True, frozen=True)
class Reading:
    reading: str
    sub_index: Optional[int]
    default: str

    @property
    def key(self):
        return self.reading, self.sub_index


def map_cleaned_reading(cleaned_reading: str) -> Union[
    str, Reading, List[Union[str, Reading]]
]:
    def map_(value):
        factories = [
            (BROKEN_PATTERN, lambda _: BROKEN_SIGN),
            (WITH_SIGN_PATTERN, lambda match: match.group(1)),
            (NUMBER_PATTERN, map_number),
            (GRAPHEME_PATTERN, lambda match: match.group(0)),
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
        ), UNKNOWN_SIGN)

    def map_number(match):
        value = match.group(0)
        return Reading(value, 1, value)

    def map_reading(match):
        sub_index = (
            unicode_to_int(match.group(2))
            if match.group(2)
            else 1
        )
        return Reading(match.group(1), sub_index, UNKNOWN_SIGN)

    def map_variant(match):
        return [
            map_(part)
            for part
            in match.group(0).split(VARIANT_SEPARATOR)
        ]

    return map_(cleaned_reading)
