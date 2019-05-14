from enum import Enum

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
MODIFIER = from_enum(Modifier)
AKKADIAN_WORD = seq(
    BROKEN_OFF_OPEN.optional(),
    AKKADIAN_ALPHABET + ((BROKEN_OFF.map(lambda broken: broken.value) +
                          AKKADIAN_ALPHABET) |
                         AKKADIAN_ALPHABET).many().concat(),
    MODIFIER.at_most(2),
    BROKEN_OFF_CLOSE.optional()
)

LACUNA = seq(BROKEN_OFF_OPEN.optional(),
             string('...'),
             BROKEN_OFF_CLOSE.optional())


CAESURA = string_from('(||)', '||')

FEET_SEPARATOR = string_from('(|)', '|')
