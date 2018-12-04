import re
import pydash


IGNORE_LINE_PATTERN = r'@|\$|#|&|=:'
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
    r'}+({+\+?)?\s*?|'
    r'-|'
    r'(^|\s+)(\||&\d*)($|\s+)'
)
BRACES_PATTERN = (
    r'(?<![^\s])'
    r'\(([^\(\)]*)\)'
    r'(?!=[^\s])'
)
VARIANT_SEPARATOR = '/'


class TransliterationError(Exception):
    def __init__(self, errors):
        super().__init__('Invalid transliteration')
        self.errors = errors


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
    if VARIANT_SEPARATOR in value:
        return _clean_variant(value)
    elif grapheme or reading_with_sign:
        return value
    else:
        return _clean_reading(value)


def _clean_variant(value):
    return VARIANT_SEPARATOR.join([
        _clean_value(part)
        for part in value.split(VARIANT_SEPARATOR)
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

    def __init__(self, atf, notes='', signs=None):
        self._atf = atf
        self._notes = notes
        self._signs = signs

    def __eq__(self, other):
        return (isinstance(other, Transliteration) and
                (self.atf == other.atf) and
                (self.notes == other.notes))

    def __hash__(self):
        return hash((self._atf, self._notes))

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
            if line and not re.match(IGNORE_LINE_PATTERN, line)
        ]

    def with_signs(self, sign_list):
        signs = '\n'.join([
            ' '.join(row)
            for row in self.to_sign_matrix(sign_list)
        ])
        return Transliteration(self.atf, self.notes, signs)

    def to_sign_matrix(self, sign_list):
        return sign_list.map_transliteration(self.cleaned)

    def tokenize(self, create_token):
        lines = self.atf.split('\n')
        return [
            [
                create_token(value)
                for value in (
                    [line]
                    if re.match(IGNORE_LINE_PATTERN, line)
                    else line.split(' ')
                )
            ]
            for line in lines
        ]
