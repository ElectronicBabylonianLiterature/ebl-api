from parsy import char_from, seq, string, string_from

BROKEN_LEFT = string_from('[(', '[', '(')
BROKEN_RIGHT = string_from(')]', ']', ')')
BROKEN = BROKEN_LEFT | BROKEN_RIGHT

AKKADIAN_ALPHABET = char_from('abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ')
MODIFIER = char_from('#?')
AKKADIAN_WORD = seq(
    BROKEN_LEFT.optional(),
    AKKADIAN_ALPHABET + ((BROKEN + AKKADIAN_ALPHABET) |
                         AKKADIAN_ALPHABET).many().concat(),
    MODIFIER.at_most(2).concat(),
    BROKEN_RIGHT.optional()
)

LACUNA = seq(BROKEN_LEFT.optional(),
             string('...'),
             BROKEN_RIGHT.optional())
