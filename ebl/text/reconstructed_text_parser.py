import pydash
from parsy import char_from, seq, string, string_from, from_enum, ParseError

from ebl.text.reconstructed_text import Modifier, BrokenOffOpen, \
    BrokenOffClose, AkkadianWord, Lacuna, Caesura, MetricalFootSeparator, \
    BrokenOffPart, StringPart

BROKEN_OFF_OPEN = from_enum(BrokenOffOpen)
BROKEN_OFF_CLOSE = from_enum(BrokenOffClose)
BROKEN_OFF = BROKEN_OFF_OPEN | BROKEN_OFF_CLOSE

AKKADIAN_ALPHABET = char_from(
    '-ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄'
)
AKKADIAN_STRING = AKKADIAN_ALPHABET.at_least(1).concat()
MODIFIER = from_enum(Modifier)
AKKADIAN_WORD = (seq(
    BROKEN_OFF_OPEN.map(BrokenOffPart).optional(),
    AKKADIAN_STRING.map(StringPart),
    seq(BROKEN_OFF.map(BrokenOffPart), AKKADIAN_STRING.map(StringPart)).many()
).map(pydash.flatten_deep) + seq(
    MODIFIER.at_most(2),
    BROKEN_OFF_CLOSE.map(BrokenOffPart).optional()
).map(pydash.reverse)).map(pydash.partial_right(pydash.reject, pydash.is_none))

LACUNA = seq(BROKEN_OFF_OPEN.optional(),
             string('...'),
             BROKEN_OFF_CLOSE.optional())


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
