import pydash
from parsy import char_from, seq, string, string_from, from_enum, ParseError

from ebl.text.reconstructed_text import Modifier, BrokenOffOpen, \
    BrokenOffClose, AkkadianWord, Lacuna, Caesura, MetricalFootSeparator, \
    BrokenOffPart, StringPart, LacunaPart, SeparatorPart


ELLIPSIS = string('...')

BROKEN_OFF_OPEN = from_enum(BrokenOffOpen)
BROKEN_OFF_CLOSE = from_enum(BrokenOffClose)
BROKEN_OFF = BROKEN_OFF_OPEN | BROKEN_OFF_CLOSE

AKKADIAN_ALPHABET = char_from(
    'ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄'
)

AKKADIAN_STRING = AKKADIAN_ALPHABET.at_least(1).concat()

SEPARATOR_PART = string('-').map(lambda _: SeparatorPart())
BROKEN_OFF_OPEN_PART = BROKEN_OFF_OPEN.map(BrokenOffPart)
BROKEN_OFF_CLOSE_PART = BROKEN_OFF_CLOSE.map(BrokenOffPart)
BROKEN_OFF_PART = BROKEN_OFF.map(BrokenOffPart)
LACUNA_PART = ELLIPSIS.map(lambda _: LacunaPart())
STRING_PART = AKKADIAN_STRING.map(StringPart)
BETWEEN_STRINGS = (seq(BROKEN_OFF_PART, SEPARATOR_PART) |
                   seq(SEPARATOR_PART, BROKEN_OFF_PART) |
                   BROKEN_OFF_PART |
                   SEPARATOR_PART)
MODIFIER = from_enum(Modifier)
AKKADIAN_WORD = (seq(
    BROKEN_OFF_OPEN_PART.optional(),
    seq(LACUNA_PART, BETWEEN_STRINGS.optional()).optional(),
    STRING_PART,
    (
        seq(BETWEEN_STRINGS, STRING_PART | LACUNA_PART) |
        seq(LACUNA_PART, BETWEEN_STRINGS.optional(), STRING_PART) |
        STRING_PART
    ).many(),
    seq(BETWEEN_STRINGS.optional(), LACUNA_PART).optional()
).map(pydash.flatten_deep) + seq(
    MODIFIER.at_most(3).map(pydash.uniq),
    BROKEN_OFF_CLOSE_PART.optional()
).map(pydash.reverse)).map(pydash.partial_right(pydash.reject, pydash.is_none))

LACUNA = seq(BROKEN_OFF_OPEN.optional(), ELLIPSIS, BROKEN_OFF_CLOSE.optional())


CAESURA = string_from('(||)', '||')

FOOT_SEPARATOR = string_from('(|)', '|')

WORD_SEPARATOR = string(' ')
BREAK = (CAESURA.map(lambda token:
                     Caesura(False) if token == '||' else Caesura(True)) |
         FOOT_SEPARATOR.map(lambda token: MetricalFootSeparator(False)
                            if token == '|'
                            else MetricalFootSeparator(True)))
TEXT_PART = (
    AKKADIAN_WORD.map(lambda token: AkkadianWord(tuple(token[:-1]),
                                                 tuple(token[-1]))) |
    LACUNA.map(lambda token: Lacuna((token[0], token[2])))
).at_least(1).sep_by(WORD_SEPARATOR)

RECONSTRUCTED_LINE = (
    TEXT_PART +
    seq(WORD_SEPARATOR >> BREAK << WORD_SEPARATOR, TEXT_PART).many()
).map(pydash.flatten_deep)


def parse_reconstructed_line(text: str):
    try:
        return tuple(RECONSTRUCTED_LINE.parse(text))
    except ParseError as error:
        raise ValueError(f'Invalid reconstructed line: {text}. {error}')
