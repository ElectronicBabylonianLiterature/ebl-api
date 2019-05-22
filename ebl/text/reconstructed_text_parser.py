# type: ignore
import pydash
from parsy import ParseError, char_from, from_enum, seq, string, string_from

from ebl.text.enclosure import BROKEN_OFF_OPEN, MAYBE_BROKEN_OFF_OPEN, \
    BROKEN_OFF_CLOSE, MAYBE_BROKEN_OFF_CLOSE
from ebl.text.reconstructed_text import AkkadianWord, Caesura, EnclosurePart, \
    Lacuna, LacunaPart, MetricalFootSeparator, Modifier, SeparatorPart, \
    StringPart

ELLIPSIS = string('...')

ENCLOSURE_OPEN = (
    string('[').map(lambda _: BROKEN_OFF_OPEN) |
    string('(').map(lambda _: MAYBE_BROKEN_OFF_OPEN)
)
ENCLOSURE_CLOSE = (
    string(']').map(lambda _: BROKEN_OFF_CLOSE) |
    string(')').map(lambda _: MAYBE_BROKEN_OFF_CLOSE)
)
ENCLOSURE = ENCLOSURE_OPEN | ENCLOSURE_CLOSE

AKKADIAN_ALPHABET = char_from(
    'ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄'
)

AKKADIAN_STRING = AKKADIAN_ALPHABET.at_least(1).concat()

SEPARATOR_PART = string('-').map(lambda _: SeparatorPart())
BROKEN_OFF_OPEN_PART = ENCLOSURE_OPEN.map(EnclosurePart)
BROKEN_OFF_CLOSE_PART = ENCLOSURE_CLOSE.map(EnclosurePart)
BROKEN_OFF_PART = ENCLOSURE.map(EnclosurePart)
LACUNA_PART = ELLIPSIS.map(lambda _: LacunaPart())
STRING_PART = AKKADIAN_STRING.map(StringPart)
BETWEEN_STRINGS = (seq(BROKEN_OFF_PART.at_least(1), SEPARATOR_PART) |
                   seq(SEPARATOR_PART, BROKEN_OFF_PART.at_least(1)) |
                   BROKEN_OFF_PART.at_least(1) |
                   SEPARATOR_PART)
MODIFIER = from_enum(Modifier)
AKKADIAN_WORD = (
    seq(
        BROKEN_OFF_OPEN_PART.many(),
        seq(LACUNA_PART, BETWEEN_STRINGS.optional()).optional(),
        STRING_PART,
        (
            seq(BETWEEN_STRINGS, STRING_PART | LACUNA_PART) |
            seq(LACUNA_PART, BETWEEN_STRINGS.optional(), STRING_PART) |
            STRING_PART
        ).many(),
        seq(BETWEEN_STRINGS.optional(), LACUNA_PART).optional()
    ).map(pydash.flatten_deep) + seq(
        MODIFIER.at_most(3).map(pydash.uniq).map(lambda f: [f]),
        BROKEN_OFF_CLOSE_PART.many()
    ).map(pydash.reverse).map(pydash.flatten)
).map(pydash.partial_right(pydash.reject, pydash.is_none))

LACUNA = seq(ENCLOSURE_OPEN.many(), ELLIPSIS, ENCLOSURE_CLOSE.many())


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
    LACUNA.map(lambda token: Lacuna(tuple(token[0]), tuple(token[2])))
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
