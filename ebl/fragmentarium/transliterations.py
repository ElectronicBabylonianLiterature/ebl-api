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


def clean(transliteration):
    return (
        pydash
        .chain(transliteration)
        .thru(filter_lines)
        .map(_clean_line)
        .map(_clean_values)
        .value()
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


def filter_lines(transliteration):
    return [
        line
        for line in transliteration.split('\n')
        if line and not re.match(r'@|\$|#|&|=:', line)
    ]
