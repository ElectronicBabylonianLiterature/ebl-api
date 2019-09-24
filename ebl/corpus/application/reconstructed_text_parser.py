from typing import Optional

import pydash
from parsy import ParseError, alt, char_from, from_enum, seq, string, \
    string_from

from ebl.corpus.domain.enclosure import Enclosure, EnclosureType, \
    EnclosureVariant
from ebl.corpus.domain.reconstructed_text import AkkadianWord, Caesura, \
    EnclosurePart, \
    Lacuna, LacunaPart, MetricalFootSeparator, Modifier, SeparatorPart, \
    StringPart

ELLIPSIS = string('...')


def enclosure_side(type_: EnclosureType, variant: EnclosureVariant):
    return (string(type_.get_delimiter(variant))
            .map(lambda _: Enclosure(type_, variant)))


def enclosure(variant: Optional[EnclosureVariant] = None):
    variants = [variant] if variant else [variant
                                          for variant
                                          in EnclosureVariant]
    sides = [enclosure_side(type_, variant)
             for type_ in EnclosureType
             for variant in variants]
    return alt(*sides)


def akkadian_string():
    akkadian_alphabet = char_from(
        'ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄'
    )
    return akkadian_alphabet.at_least(1).concat()


def akkadian_word():
    separator_part = string('-').map(lambda _: SeparatorPart())
    broken_off_open_part = enclosure(EnclosureVariant.OPEN).map(EnclosurePart)
    broken_off_close_part = (enclosure(EnclosureVariant.CLOSE)
                             .map(EnclosurePart))
    broken_off_part = enclosure().map(EnclosurePart)
    lacuna_part = ELLIPSIS.map(lambda _: LacunaPart())
    string_part = akkadian_string().map(StringPart)
    between_strings = (seq(broken_off_part.at_least(1), separator_part) |
                       seq(separator_part, broken_off_part.at_least(1)) |
                       broken_off_part.at_least(1) |
                       separator_part)
    modifier = from_enum(Modifier)
    return (
        seq(
            broken_off_open_part.many(),
            seq(lacuna_part, between_strings.optional()).optional(),
            string_part,
            (
                seq(between_strings, string_part | lacuna_part) |
                seq(lacuna_part, between_strings.optional(), string_part) |
                string_part
            ).many(),
            seq(between_strings.optional(), lacuna_part).optional()
        ).map(pydash.flatten_deep) + seq(
            modifier.at_most(3).map(pydash.uniq).map(lambda f: [f]),
            broken_off_close_part.many()
        ).map(pydash.reverse).map(pydash.flatten)
    ).map(pydash.partial_right(pydash.reject, pydash.is_none))


def lacuna():
    return seq(enclosure(EnclosureVariant.OPEN).many(),
               ELLIPSIS,
               enclosure(EnclosureVariant.CLOSE).many())


CAESURA = '||'


def caesura():
    return string_from(f'({CAESURA})', CAESURA)


FOOT_SEPARATOR = '|'


def foot_separator():
    return string_from(f'({FOOT_SEPARATOR})', FOOT_SEPARATOR)


def reconstructed_line():
    break_ = (caesura().map(lambda token: Caesura(False)
                            if token == CAESURA
                            else Caesura(True)) |
              foot_separator().map(lambda token: MetricalFootSeparator(False)
                                   if token == FOOT_SEPARATOR
                                   else MetricalFootSeparator(True)))
    word_separator = string(' ')
    text_part = (
        akkadian_word().map(lambda token: AkkadianWord(tuple(token[:-1]),
                                                       tuple(token[-1]))) |
        lacuna().map(lambda token: Lacuna(tuple(token[0]), tuple(token[2])))
    ).at_least(1).sep_by(word_separator)

    return (
        text_part +
        seq(word_separator >> break_ << word_separator, text_part).many()
    ).map(pydash.flatten_deep)


def parse_reconstructed_line(text: str):
    try:
        return tuple(reconstructed_line().parse(text))
    except ParseError as error:
        raise ValueError(f'Invalid reconstructed line: {text}. {error}')
