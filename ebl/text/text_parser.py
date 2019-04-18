import re

import pydash
from parsy import (char_from, decimal_digit, regex, seq, string, string_from)

import ebl.text.atf
from ebl.text.line import TextLine
from ebl.text.token import (DocumentOrientedGloss, LanguageShift,
                            LineContinuation, LoneDeterminative, Partial,
                            Token, Word)


def sequence(prefix, part, joiner, min_=None):
    joiner_and_part = joiner + part
    tail = (
        joiner_and_part.many().concat()
        if min_ is None
        else joiner_and_part.at_least(min_).concat()
    )
    return prefix + tail


def variant(parser):
    variant_separator = string(
        ebl.text.atf.VARIANT_SEPARATOR
    ).desc('variant separator')
    return sequence(parser, parser, variant_separator)


def determinative(parser):
    return (
        OMISSION.at_most(1).concat() +
        string_from('{+', '{') +
        parser +
        string('}') +
        MODIFIER +
        FLAG +
        OMISSION.at_most(1).concat()
    )


def value_sequence(prefix, part, min_=None):
    return sequence(prefix, part, JOINER.many().concat(), min_)


def true_joiner():
    def make_expression(joiner):
        escaped = re.escape(joiner)
        return (
            f'((?<=\\.\\.\\.)|(?<!{escaped}))'
            f'({escaped})'
            f'((?!{escaped})|(?=\\.\\.\\.))'
        )

    joiners = '|'.join(
        make_expression(joiner)
        for joiner
        in ebl.text.atf.JOINERS
    )
    return regex(joiners)


OMISSION = string_from(
    '<<', '<(', '<', '>>', ')>', '>'
).desc('omission or removal')
LINGUISTIC_GLOSS = string_from('{{', '}}')
DOCUMENT_ORIENTED_GLOSS = string_from('{(', ')}')
SINGLE_DOT = regex(r'(?<!\.)\.(?!\.)')
JOINER = (
        OMISSION |
        LINGUISTIC_GLOSS |
        true_joiner()
).desc('joiner')
FLAG = char_from('!?*#').many().concat().desc('flag')
MODIFIER = (
    string('@') +
    (char_from('cfgstnzkrhv') | decimal_digit.at_least(1).concat())
).many().concat()
WORD_SEPARATOR = string(ebl.text.atf.WORD_SEPARATOR).desc('word separtor')
WORD_SEPARATOR_OR_EOL = WORD_SEPARATOR | regex(r'(?=\n|$)')
LINE_NUMBER = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
TABULATION = string('($___$)').desc('tabulation')
COLUMN = regex(r'&\d*').desc('column') << WORD_SEPARATOR_OR_EOL
COMMENTARY_PROTOCOL = regex(r'!(qt|bs|cm|zz)').desc('commentary protocol')
LACUNA = regex(r'\[?\(?\.\.\.\)?\]?').desc('lacuna')
SHIFT = regex(r'%\w+').desc('language or register/writing system shift')
SUB_INDEX = regex(r'[₀-₉ₓ]+').desc('subindex')
INLINE_BROKEN_LEFT = regex(r'(\[\(|\[|(?!>{)\()(?!\.)')
INLINE_BROKEN_RIGHT = regex(r'(?<!\.)(\)\]|\)(?!})|\])')
INLINE_BROKEN = INLINE_BROKEN_LEFT | INLINE_BROKEN_RIGHT
DIVIDER = (
    INLINE_BROKEN.at_most(1).concat() +
    string_from('|', ':\'', ':"', ':.', '::', ':?', ':', ';', '/') +
    MODIFIER +
    FLAG +
    INLINE_BROKEN.at_most(1).concat()
).desc('divider')
UNKNOWN = (
    INLINE_BROKEN.at_most(1).concat() +
    string_from(ebl.text.atf.UNIDENTIFIED_SIGN, ebl.text.atf.UNCLEAR_SIGN) +
    FLAG +
    INLINE_BROKEN.at_most(1).concat()
).desc('unclear or unidentified')
VALUE_CHAR = char_from('aāâbdeēêghiīîyklmnpqrsṣštṭuūûwzḫʾ')
VALUE = seq(
    (
        (INLINE_BROKEN + VALUE_CHAR + INLINE_BROKEN) |
        (INLINE_BROKEN + VALUE_CHAR) |
        (VALUE_CHAR + INLINE_BROKEN) |
        VALUE_CHAR |
        decimal_digit
    ).at_least(1).concat(),
    SUB_INDEX.optional(),
    MODIFIER,
    FLAG,
    INLINE_BROKEN.at_most(1).concat()
).map(pydash.compact).concat().desc('reading')
GRAPHEME_CHAR = regex(r'[A-ZṢŠṬa-zṣšṭ0-9₀-₉]')
GRAPHEME = (
    string('$').at_most(1).concat() +
    (
        (INLINE_BROKEN + GRAPHEME_CHAR + INLINE_BROKEN) |
        (INLINE_BROKEN + GRAPHEME_CHAR) |
        (GRAPHEME_CHAR + INLINE_BROKEN) |
        GRAPHEME_CHAR
    ).at_least(1).concat() +
    MODIFIER +
    FLAG +
    INLINE_BROKEN.at_most(1).concat()
).desc('grapheme')
COMPOUND_GRAPHEME_OPERATOR = (SINGLE_DOT | char_from('×%&+()')).desc(
    'compound grapheme operator'
)
COMPOUND_DELIMITER = string('|').at_most(1).concat()
COMPOUND_PART = variant(GRAPHEME)
COMPOUND_GRAPHEME = (
    seq(
        COMPOUND_DELIMITER,
        COMPOUND_PART,
        (
                COMPOUND_GRAPHEME_OPERATOR.many().concat() +
                COMPOUND_PART
        ).many().concat(),
        COMPOUND_DELIMITER
    )
    .map(pydash.flatten_deep)
    .concat()
    .desc('compound grapheme')
)
VALUE_WITH_SIGN = (
    VALUE +
    string('!').at_most(1).concat() +
    string('(') +
    COMPOUND_GRAPHEME +
    string(')')
)
VARIANT = variant(
    UNKNOWN |
    VALUE_WITH_SIGN |
    VALUE |
    COMPOUND_GRAPHEME |
    GRAPHEME |
    DIVIDER
)
DETERMINATIVE_SEQUENCE = (
    INLINE_BROKEN.at_most(1).concat() +
    determinative(value_sequence(VARIANT, VARIANT)) +
    INLINE_BROKEN.at_most(1).concat()
)
WORD = seq(
    JOINER.many().concat(),
    (
        value_sequence(VARIANT, DETERMINATIVE_SEQUENCE | VARIANT) |
        value_sequence(
            DETERMINATIVE_SEQUENCE, DETERMINATIVE_SEQUENCE | VARIANT, 1
        )
    ),
    JOINER.many().concat(),
    FLAG
).map(pydash.flatten_deep).concat().desc('word')
LONE_DETERMINATIVE = determinative(
    VARIANT + (JOINER.many().concat() + VARIANT).many().concat()
).desc('lone determinative')
LINE_CONTINUATION = string('→').map(LineContinuation).desc('line continuation')

TEXT_LINE = seq(
    LINE_NUMBER << WORD_SEPARATOR,
    (
        TABULATION.map(Token) |
        COLUMN.map(Token) |
        (DIVIDER << WORD_SEPARATOR_OR_EOL).map(Token) |
        COMMENTARY_PROTOCOL.map(Token) |
        DOCUMENT_ORIENTED_GLOSS.map(DocumentOrientedGloss) |
        SHIFT.map(LanguageShift) |
        WORD.map(Word) |
        seq(LACUNA, LONE_DETERMINATIVE, LACUNA).map(
            lambda values: [
                Token(values[0]),
                LoneDeterminative.of_value(
                    values[1], Partial(True, True)
                ),
                Token(values[2])
            ]
        ) |
        seq(LACUNA, LONE_DETERMINATIVE).map(
            lambda values: [
                Token(values[0]),
                LoneDeterminative.of_value(
                    values[1], Partial(True, False)
                )
            ]
        ) |
        seq(LONE_DETERMINATIVE, LACUNA).map(
            lambda values: [
                LoneDeterminative.of_value(
                    values[0], Partial(False, True)
                ),
                Token(values[1])
            ]
        ) |
        LONE_DETERMINATIVE.map(
            lambda value: LoneDeterminative.of_value(
                value, Partial(False, False)
            )
        ) |
        LACUNA.map(Token) |
        OMISSION.map(Token)
    ).many().sep_by(WORD_SEPARATOR).map(pydash.flatten_deep) +
    (LINE_CONTINUATION << WORD_SEPARATOR.many().concat()).at_most(1),
).combine(TextLine.of_iterable)
