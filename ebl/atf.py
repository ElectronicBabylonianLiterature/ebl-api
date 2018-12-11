from pyoracc.atf.common.atffile import AtfFile


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
    'with_sign': r'[^\(/\|]+\((.+)\)|',
    'grapheme': r'\|?(\d*[.x×%&+@]?\(?[A-ZṢŠṬ₀-₉ₓ]+([@~][a-z0-9]+)*\)?)+\|?',
    'number': r'\d+',
    'variant': r'([^/]+)(?:/([^/]+))+',
    'unclear': 'x',
    'unindentified': 'X',
    'joiner': '-',
    'word_separator': ' ',
    'variant_separator': '/'
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
    def __init__(self, source):
        self.line_number = source.lineno - len(ATF_HEADING)
        self.text = source.text
        message = f"Line {self.line_number} is invalid."
        super().__init__(message)


def validate_atf(text):
    prefix = '\n'.join(ATF_HEADING)
    try:
        AtfFile(f'{prefix}\n{text}', atftype='oracc')
    except SyntaxError as error:
        raise AtfSyntaxError(error)
    except (IndexError,
            AttributeError,
            UnicodeDecodeError) as error:
        raise AtfError(error)
