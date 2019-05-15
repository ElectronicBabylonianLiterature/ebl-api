from enum import Enum

import pydash
from parsy import char_from, seq, string, string_from, from_enum


class Modifier(Enum):
    BROKEN = '#'
    UNCERTAIN = '?'


class BrokenOffOpen(Enum):
    BOTH = '[('
    BROKEN = '['
    MAYBE = '('


class BrokenOffClose(Enum):
    BOTH = ')]'
    BROKEN = ']'
    MAYBE = ')'


BROKEN_OFF_OPEN = from_enum(BrokenOffOpen)
BROKEN_OFF_CLOSE = from_enum(BrokenOffClose)
BROKEN_OFF = BROKEN_OFF_OPEN | BROKEN_OFF_CLOSE

AKKADIAN_ALPHABET = char_from('abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ')
AKKADIAN_STRING = AKKADIAN_ALPHABET.at_least(1).concat()
MODIFIER = from_enum(Modifier)
AKKADIAN_WORD = (seq(
    BROKEN_OFF_OPEN.optional(),
    AKKADIAN_STRING,
    seq(BROKEN_OFF, AKKADIAN_STRING).many()
).map(pydash.flatten_deep) + seq(
    MODIFIER.at_most(2),
    BROKEN_OFF_CLOSE.optional()
).map(pydash.reverse)).map(pydash.partial_right(pydash.reject, pydash.is_none))

LACUNA = seq(BROKEN_OFF_OPEN.optional(),
             string('...'),
             BROKEN_OFF_CLOSE.optional())


CAESURA = string_from('(||)', '||')

FEET_SEPARATOR = string_from('(|)', '|')
