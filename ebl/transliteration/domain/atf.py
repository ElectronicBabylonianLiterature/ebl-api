from enum import Enum
from typing import Mapping, NewType

import pydash
from pyoracc.atf.common.atffile import AtfFile

Atf = NewType('Atf', str)


ATF_PARSER_VERSION = '0.17.0'
DEFAULT_ATF_PARSER_VERSION = '0.1.0'


class AtfError(Exception):
    pass


class AtfSyntaxError(AtfError):
    def __init__(self, line_number):
        self.line_number = line_number
        message = f"Line {self.line_number} is invalid."
        super().__init__(message)


def validate_atf(text):
    prefix = '\n'.join(ATF_HEADING)
    try:
        return AtfFile(f'{prefix}\n{text}', atftype='oracc')
    except SyntaxError as error:
        line_number = error.lineno - len(ATF_HEADING)
        raise AtfSyntaxError(line_number)
    except (IndexError,
            AttributeError,
            UnicodeDecodeError) as error:
        raise AtfError(error)


class Surface(Enum):
    """ See "Surface" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    """

    OBVERSE = ('@obverse', 'o')
    REVERSE = ('@reverse', 'r')
    BOTTOM = ('@bottom', 'b.e.')
    EDGE = ('@edge', 'e.')
    LEFT = ('@left', 'l.e.')
    RIGHT = ('@right', 'r.e.')
    TOP = ('@top', 't.e.')

    def __init__(self, atf, label):
        self.atf = atf
        self.label = label

    @staticmethod
    def from_label(label: str) -> 'Surface':
        return [
            enum for enum in Surface
            if enum.label == label
        ][0]

    @staticmethod
    def from_atf(atf: str) -> 'Surface':
        return [
            enum for enum in Surface
            if enum.atf == atf
        ][0]


class Status(Enum):
    """ See "Status" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html
    """

    PRIME = "'"
    UNCERTAIN = '?'
    CORRECTION = '!'
    COLLATION = '*'


class CommentaryProtocol(Enum):
    """ See
    http://oracc.museum.upenn.edu/doc/help/editinginatf/commentary/index.html
    """

    QUOTATION = '!qt'
    BASE_TEXT = '!bs'
    COMMENTARY = '!cm'
    UNCERTAIN = '!zz'


class Flag(Enum):
    """ See "Metadata" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html
    """

    DAMAGE = '#'
    UNCERTAIN = '?'
    CORRECTION = '!'
    COLLATION = '*'


class Joiner(Enum):
    HYPHEN = '-'
    DOT = '.'
    PLUS = '+'
    COLON = ':'


UNKNOWN_NUMBER_OF_SIGNS = '...'
WORD_SEPARATOR = ' '
VARIANT_SEPARATOR = '/'
UNCLEAR_SIGN = 'x'
UNIDENTIFIED_SIGN = 'X'

FLAGS: Mapping[str, str] = {
    'uncertainty': pydash.escape_reg_exp(Flag.UNCERTAIN.value),
    'collation': pydash.escape_reg_exp(Flag.COLLATION.value),
    'damage': pydash.escape_reg_exp(Flag.DAMAGE.value),
    'correction': pydash.escape_reg_exp(Flag.CORRECTION.value),
    'not_logogram': r'\$',
}

LACUNA: Mapping[str, str] = {
    'begin': r'\[',
    'end': r'\]',
    'undeterminable': pydash.escape_reg_exp(UNKNOWN_NUMBER_OF_SIGNS)
}

ATF_SPEC: Mapping[str, str] = {
    'reading': r'([^₀-₉ₓ/]+)([₀-₉]+)?',
    'with_sign': r'[^\(/\|]+\((.+)\)',
    'grapheme':
        r'\|([.x×%&+@]?(\d+[.x×%&+@])?\(?[A-ZṢŠṬ₀-₉ₓ]+([@~][a-z0-9]+)*\)?)+\|',
    'number': r'\d+',
    'variant': r'([^/]+)(?:/([^/]+))+',
}

ATF_EXTENSIONS: Mapping[str, str] = {
    'erasure_boundary': '°',
    'erasure_delimiter': '\\',
    'erasure_illegible': r'°[^\°]*\\',
    'line_continuation': '→',
}


ATF_HEADING = [
    '&XXX = XXX',
    '#project: eblo',
    '#atf: lang akk-x-stdbab',
    '#atf: use unicode',
    '#atf: use math',
    '#atf: use legacy'
]
