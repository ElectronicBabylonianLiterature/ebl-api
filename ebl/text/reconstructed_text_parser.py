
from parsy import char_from, seq

from ebl.text.text_parser import INLINE_BROKEN_LEFT, INLINE_BROKEN, \
    INLINE_BROKEN_RIGHT

AKKADIAN_ALPHABET = char_from('abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ')
MODIFIER = char_from('#?')

AKKADIAN_WORD = seq(
    INLINE_BROKEN_LEFT.optional(),
    AKKADIAN_ALPHABET + (
        (INLINE_BROKEN + AKKADIAN_ALPHABET) | AKKADIAN_ALPHABET
    ).many().concat(),
    MODIFIER.at_most(2).concat(),
    INLINE_BROKEN_RIGHT.optional()
)
