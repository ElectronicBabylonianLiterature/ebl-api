from enum import Enum
from typing import NewType

from pyoracc.atf.common.atffile import AtfFile

Atf = NewType('Atf', str)


WORD_SEPARATOR = ' '
HYPHEN = '-'
JOINERS = [HYPHEN, '+', '.']
VARIANT_SEPARATOR = '/'
UNCLEAR_SIGN = 'x'
UNIDENTIFIED_SIGN = 'X'


ATF_SPEC = {
    'line_number': r'^[^\.]+\.([^\.]+\.)?',
    'shift': r'%\w+',
    'control_line': r'^(@|\$(( ?(single|double|triple))| )|#|&)',
    'multiplex_comment': r'=:',
    'tabulation': r'\(\$_+\$\)',
    'divider': r'(^|\s+)(\||&\d*)($|\s+)',
    'flags': {
        'uncertainty': r'\?',
        'collation': r'\*',
        'damage': r'#',
        'correction': r'!',
        'not_logogram': r'\$',
    },
    'lacuna': {
        'begin': r'\[',
        'end': r'\]',
        'undeterminable': r'\.\.\.'
    },
    'alternative_damage': r'[⸢⸣]',
    'determinative_or_gloss': {
        'begin': r'\s*{+\+?',
        'end': r'}+({+\+?)?\s*?'
    },
    'omission': r'<\(?[^>]+\)?>',
    'removal': r'<<[^>]+>>',
    'reading': r'([^₀-₉ₓ/]+)([₀-₉]+)?',
    'with_sign': r'[^\(/\|]+\((.+)\)',
    'grapheme': r'\|?(\d*[.x×%&+@]?\(?[A-ZṢŠṬ₀-₉ₓ]+([@~][a-z0-9]+)*\)?)+\|?',
    'number': r'\d+',
    'variant': r'([^/]+)(?:/([^/]+))+',
    'unclear': UNCLEAR_SIGN,
    'unidentified': UNIDENTIFIED_SIGN,
    'joiner': HYPHEN,
    'word_separator': WORD_SEPARATOR,
    'variant_separator': VARIANT_SEPARATOR,
}

ATF_EXTENSIONS = {
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
