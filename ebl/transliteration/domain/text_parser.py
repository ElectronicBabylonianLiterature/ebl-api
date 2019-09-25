import re

import pydash
from parsy import (char_from, decimal_digit, regex, seq, string, string_from)

import ebl.atf.domain.atf
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import TextLine
from ebl.transliteration.domain.token import (BrokenAway,
                                              DocumentOrientedGloss,
                                              Erasure,
                                              ErasureState, LanguageShift,
                                              LineContinuation,
                                              LoneDeterminative,
                                              OmissionOrRemoval,
                                              Partial,
                                              PerhapsBrokenAway, Side, Token,
                                              Word)


def sequence(prefix, part, joiner, min_=0):
    joiner_and_part = joiner + part
    tail = (
        joiner_and_part.many().concat()
        if min_ is None
        else joiner_and_part.at_least(min_).concat()
    )
    return prefix + tail


def variant(parser):
    variant_separator = string(
        ebl.atf.domain.atf.VARIANT_SEPARATOR
    ).desc('variant separator')
    return sequence(parser, parser, variant_separator)


def determinative(parser):
    return (
        OMISSION.at_most(1).concat() +
        string_from('{+', '{') +
        BROKEN_AWAY_LEFT.at_most(1).concat() +
        parser +
        BROKEN_AWAY_RIGHT.at_most(1).concat() +
        string('}') +
        OMISSION.at_most(1).concat()
    )


def value_sequence(prefix, part, min_=None):
    return sequence(prefix,
                    part,
                    (INLINE_BROKEN_RIGHT.at_most(1).concat() +
                     OMISSION_RIGHT.at_most(1).concat() +
                     JOINER.many().concat() +
                     OMISSION_LEFT.at_most(1).concat() +
                     INLINE_BROKEN_LEFT.at_most(1).concat()),
                    min_)


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
        in ebl.atf.domain.atf.JOINERS
    )
    return regex(joiners)


OMISSION_LEFT = string_from('<<', '<(', '<').desc('left omission or removal')
OMISSION_RIGHT = string_from('>>', ')>', '>').desc('right omission or removal')
OMISSION = (OMISSION_LEFT | OMISSION_RIGHT).desc('omission or removal')
LINGUISTIC_GLOSS_LEFT = string_from('{{')
LINGUISTIC_GLOSS_RIGHT = string_from('}}')
DOCUMENT_ORIENTED_GLOSS = string_from('{(', ')}')
SINGLE_DOT = regex(r'(?<!\.)\.(?!\.)')
JOINER = (
    LINGUISTIC_GLOSS_RIGHT |
    true_joiner() |
    LINGUISTIC_GLOSS_LEFT
).desc('joiner')
FLAG = char_from('!?*#').many().concat().desc('flag')
MODIFIER = (
    string('@') +
    (char_from('cfgstnzkrhv') | decimal_digit.at_least(1).concat())
).many().concat()
WORD_SEPARATOR =\
    string(ebl.atf.domain.atf.WORD_SEPARATOR).desc('word separtor')
WORD_SEPARATOR_OR_EOL = WORD_SEPARATOR | regex(r'(?=\n|$)')
LINE_NUMBER = regex(r'[^\s]+\.').map(
    LineNumberLabel.from_atf
).desc('line number')
TABULATION = string('($___$)').desc('tabulation')
COLUMN = regex(r'&\d*').desc('column') << WORD_SEPARATOR_OR_EOL
COMMENTARY_PROTOCOL = regex(r'!(qt|bs|cm|zz)').desc('commentary protocol')
UNKNOWN_NUMBER_OF_SIGNS = string('...')
SHIFT = regex(r'%\w+').desc('language or register/writing system shift')
SUB_INDEX = regex(r'[₀-₉ₓ]+').desc('subindex')
BROKEN_AWAY_LEFT = string('[')
BROKEN_AWAY_RIGHT = string(']')
BROKEN_AWAY = BROKEN_AWAY_LEFT | BROKEN_AWAY_RIGHT
PERHAPS_BROKEN_AWAY_LEFT = string('(')
PERHAPS_BROKEN_AWAY_RIGHT = string(')')
PERHAPS_BROKEN_AWAY = PERHAPS_BROKEN_AWAY_LEFT | PERHAPS_BROKEN_AWAY_RIGHT
INLINE_BROKEN_LEFT = regex(r'(\[\(|\[|(?<!{)\()(?!\.)')
INLINE_BROKEN_RIGHT = regex(r'(?<!\.)(\)\]|\)(?!})|\])')
INLINE_BROKEN = INLINE_BROKEN_LEFT | INLINE_BROKEN_RIGHT
DIVIDER = (
    string_from('|', ':\'', ':"', ':.', '::', ':?', ':', ';', '/') +
    MODIFIER +
    FLAG
).desc('divider')
UNKNOWN = (
        string_from(ebl.atf.domain.atf.UNIDENTIFIED_SIGN,
                    ebl.atf.domain.atf.UNCLEAR_SIGN) +
        FLAG
).desc('unclear or unidentified')
VALUE_CHAR = char_from('aāâbdeēêghiīîyklmnpqrsṣštṭuūûwzḫʾ')
VALUE = seq(
    (VALUE_CHAR | decimal_digit),
    (
        INLINE_BROKEN.at_most(1).concat() +
        (VALUE_CHAR | decimal_digit)
    ).many().concat(),
    SUB_INDEX.optional(),
    MODIFIER,
    FLAG,
).map(pydash.compact).concat().desc('reading')
GRAPHEME_CHAR = regex(r'[A-ZṢŠṬa-zṣšṭ0-9₀-₉]')
GRAPHEME = (
    string('$').at_most(1).concat() + GRAPHEME_CHAR +
    (
        INLINE_BROKEN.at_most(1).concat() +
        GRAPHEME_CHAR
    ).many().concat() +
    MODIFIER +
    FLAG
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
DETERMINATIVE_SEQUENCE = determinative(value_sequence(VARIANT, VARIANT))

WORD_PARTS = (
        value_sequence(VARIANT,
                       DETERMINATIVE_SEQUENCE | VARIANT) |
        value_sequence(DETERMINATIVE_SEQUENCE,
                       DETERMINATIVE_SEQUENCE | VARIANT, 1)
)


def erasure_part(state: ErasureState):
    return ((DIVIDER.map(Token) |
             WORD.map(lambda value: Word(value, erasure=state)) |
             LONE_DETERMINATIVE.map(lambda value: LoneDeterminative
                                    .of_value(value, Partial(False, False))))
            .many()
            .sep_by(WORD_SEPARATOR)
            .map(pydash.flatten))


def erasure(map_tokens: bool, part_parser=erasure_part):
    return (seq(string(ebl.atf.domain.atf.ATF_EXTENSIONS['erasure_boundary'])
                .map(lambda value: Erasure(value, Side.LEFT)
                     if map_tokens else value),
                part_parser(ErasureState.ERASED),
                string(ebl.atf.domain.atf.ATF_EXTENSIONS['erasure_delimiter'])
                .map(lambda value: Erasure(value, Side.CENTER)
                     if map_tokens else value),
                part_parser(ErasureState.OVER_ERASED),
                string(ebl.atf.domain.atf.ATF_EXTENSIONS['erasure_boundary'])
                .map(lambda value: Erasure(value, Side.RIGHT)
                     if map_tokens else value))
            .desc('erasure'))


PARTS_WITH_ERASURE = erasure(False, lambda _:  WORD_PARTS
                             .many()).map(pydash.flatten_deep).concat() | \
                     WORD_PARTS.map(pydash.flatten_deep).concat()
WORD = seq(
    (
            JOINER.at_least(1).concat() +
            INLINE_BROKEN_LEFT.at_most(1).concat()
    ).at_most(1).concat(),
    OMISSION_LEFT.at_most(1).concat() +
    (
            value_sequence(PARTS_WITH_ERASURE, PARTS_WITH_ERASURE, 1) |
            WORD_PARTS
    ),
    OMISSION_RIGHT.at_most(1).concat() +
    (
            INLINE_BROKEN_RIGHT.at_most(1).concat() +
            JOINER.at_least(1).concat()
    ).at_most(1).concat()
).map(pydash.flatten_deep).concat().desc('word')
LONE_DETERMINATIVE = determinative(
    VARIANT + (JOINER.many().concat() + VARIANT).many().concat()
).desc('lone determinative')


LINE_CONTINUATION =\
    string('→').map(LineContinuation).desc('line continuation')

TEXT_LINE = seq(
    LINE_NUMBER << WORD_SEPARATOR,
    (
            TABULATION.map(Token) |
            COLUMN.map(Token) |
            (DIVIDER << WORD_SEPARATOR_OR_EOL).map(Token) |
            COMMENTARY_PROTOCOL.map(Token) |
            DOCUMENT_ORIENTED_GLOSS.map(DocumentOrientedGloss) |
            SHIFT.map(LanguageShift) |
            erasure(True) << WORD_SEPARATOR_OR_EOL |
            WORD.map(Word) |
            seq(
                (UNKNOWN_NUMBER_OF_SIGNS.map(Token) |
                 BROKEN_AWAY_RIGHT.map(BrokenAway) |
                 PERHAPS_BROKEN_AWAY_RIGHT.map(PerhapsBrokenAway)).optional(),
                LONE_DETERMINATIVE,
                (UNKNOWN_NUMBER_OF_SIGNS.map(Token) |
                 BROKEN_AWAY_LEFT.map(BrokenAway) |
                 PERHAPS_BROKEN_AWAY_LEFT.map(PerhapsBrokenAway)).optional()
            ).map(
                lambda values: [token for token in [
                    values[0],
                    LoneDeterminative.of_value(
                        values[1], Partial(values[0] is not None,
                                           values[2] is not None)
                    ),
                    values[2]
                ] if token is not None]
            ) |
            OMISSION.map(OmissionOrRemoval) |
            BROKEN_AWAY.map(BrokenAway) |
            PERHAPS_BROKEN_AWAY.map(PerhapsBrokenAway) |
            UNKNOWN_NUMBER_OF_SIGNS.map(Token)
    ).many().sep_by(WORD_SEPARATOR).map(pydash.flatten_deep) +
    (LINE_CONTINUATION << WORD_SEPARATOR.many().concat()).at_most(1)
).combine(TextLine.of_iterable)
