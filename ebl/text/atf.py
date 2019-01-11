from typing import NewType
from pyoracc.atf.common.atffile import AtfFile


Atf = NewType('Atf', str)


WORD_SEPARATOR = ' '
JOINER = '-'
VARIANT_SEPARATOR = '/'
UNCLEAR_SIGN = 'x'
UNIDENTIFIED_SIGN = 'X'


ATF_SPEC = {
    'line_number': r'^[^\.]+\.([^\.]+\.)?',
    'shift': r'%\w+',
    'control_line': r'@|\$|#|&',
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
    'unindentified': UNIDENTIFIED_SIGN,
    'joiner': JOINER,
    'word_separator': WORD_SEPARATOR,
    'variant_separator': VARIANT_SEPARATOR
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
