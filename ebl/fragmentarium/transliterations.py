import re
import pydash


STRIP_PATTERN = (
    r'^[^\.]+\.([^\.]+\.)?\s+|'
    r'<<?\(?[^>]+\)?>?>|'
    r'\[|'
    r'\]|'
    r'\.\.\.|'
    r'\(\$_+\$\)|'
    r'\?|'
    r'\*|'
    r'#|'
    r'!|'
    r'\$|'
    r'%\w+\s+'
)
WHITE_SPACE_PATTERN = (
    r'\s*{+\+?|'
    r'}+({+\+?)?\s*|'
    r'-|'
    r'(^|\s+)(\||&\d*)($|\s+)'
)
BRACES_PATTERN = (
    r'(?<![^\s])'
    r'\(([^\(\)]*)\)'
    r'(?!=[^\s])'
)


def _clean_line(line):
    return (
        pydash
        .chain(line)
        .reg_exp_replace(WHITE_SPACE_PATTERN, ' ')
        .reg_exp_replace(STRIP_PATTERN, '')
        .reg_exp_replace(BRACES_PATTERN, r'\1')
        .clean()
        .value()
    )


def _clean_values(line):
    return (
        pydash
        .chain(line)
        .split(' ')
        .map(_clean_value)
        .join(' ')
        .clean()
        .value()
    )


def _clean_value(value):
    grapheme = re.fullmatch(r'\|[^|]+\|', value)
    reading_with_sign = re.fullmatch(r'[^\(]+\(([^\)]+)\)', value)
    if '/' in value:
        return _clean_variant(value)
    elif grapheme or reading_with_sign:
        return value
    else:
        return _clean_reading(value)


def _clean_variant(value):
    return '/'.join([
        _clean_value(part)
        for part in value.split('/')
    ])


def _clean_reading(value):
    return (
        pydash.chain(value)
        .reg_exp_replace(r'[.+]', ' ')
        .reg_exp_replace(r'@[^\s]+', '')
        .value()
        .lower()
    )


class Transliteration:

    def __init__(self, atf, notes, signs=None):
        self._atf = atf
        self._notes = notes
        self._signs = signs

    def __eq__(self, other):
        return (isinstance(other, Transliteration) and
                (self.atf == other.atf) and
                (self.notes == other.notes))

    def __hash__(self):
        return hash((self._atf, self._notes))
    
    @staticmethod
    def without_notes(atf):
        return Transliteration(atf, '', None)
 
    @property
    def atf(self):
        return self._atf

    @property
    def notes(self):
        return self._notes

    @property
    def signs(self):
        return self._signs

    @property
    def cleaned(self):
        return (
            pydash
            .chain(self.filtered)
            .map(_clean_line)
            .map(_clean_values)
            .value()
        )

    @property
    def filtered(self):
        return [
            line
            for line in self.atf.split('\n')
            if line and not re.match(r'@|\$|#|&|=:', line)
        ]

    def with_signs(self, sign_list):
        signs = self.to_signs(sign_list)
        return Transliteration(self.atf, self.notes, signs=signs)
        
    def to_signs(self, sign_list):
        signs = self.to_sign_matrix(sign_list)
        return '\n'.join([
            ' '.join(row)
            for row in signs
        ])

    def to_sign_matrix(self, sign_list):
        return sign_list.map_transliteration(self.cleaned)
