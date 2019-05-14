from enum import Enum

from parsy import char_from, seq, string, string_from, from_enum


class Modifier(Enum):
    BROKEN = '#'
    UNCERTAIN = '?'


BROKEN_LEFT = string_from('[(', '[', '(')
BROKEN_RIGHT = string_from(')]', ']', ')')
BROKEN = BROKEN_LEFT | BROKEN_RIGHT

AKKADIAN_ALPHABET = char_from('abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ')
MODIFIER = from_enum(Modifier)
AKKADIAN_WORD = seq(
    BROKEN_LEFT.optional(),
    AKKADIAN_ALPHABET + ((BROKEN + AKKADIAN_ALPHABET) |
                         AKKADIAN_ALPHABET).many().concat(),
    MODIFIER.at_most(2),
    BROKEN_RIGHT.optional()
)

LACUNA = seq(BROKEN_LEFT.optional(),
             string('...'),
             BROKEN_RIGHT.optional())


CAESURA = string_from('(||)', '||')

FEET_SEPARATOR = string_from('(|)', '|')
