import re
from typing import List, Sequence

import attr
import pydash

from ebl.atf.atf import ATF_EXTENSIONS, Atf, FLAGS, LACUNA, \
    VARIANT_SEPARATOR, \
    WORD_SEPARATOR
from ebl.transliteration_search.value import Value
from ebl.transliteration_search.value_mapper import parse_reading

CONTROL_LINE = r'^(@|\$(( ?(single|double|triple))| )|#|&)'
MULTIPLEX_COMMENT = r'=:'
IGNORE_LINE_PATTERN = r'|'.join([CONTROL_LINE, MULTIPLEX_COMMENT])


LINE_NUMBER = r'^[^ ]+\.\s+'
OMISSION = r'<\(?[^>]+\)?>'
REMOVAL = r'<<[^>]+>>'
TABULATION = r'\(\$_+\$\)'
SHIFT = r'%\w+\s+'
ALTERNATIVE_DAMAGE = r'[⸢⸣]'
STRIP_PATTERN = r'|'.join([
    ATF_EXTENSIONS['erasure_illegible'],
    ATF_EXTENSIONS['erasure_boundary'],
    *FLAGS.values(),
    *LACUNA.values(),
    LINE_NUMBER,
    REMOVAL,
    OMISSION,
    TABULATION,
    SHIFT,
    ATF_EXTENSIONS['line_continuation'],
    ALTERNATIVE_DAMAGE
])


DETERMINATIVE_OR_GLOSS = {
    'begin': r'\s*{+\+?',
    'end': r'}+({+\+?)?\s*?'
}
DIVIDER = r'(^|\s+)(\||&\d*)($|\s+)'
JOINER = '-'
WHITE_SPACE_PATTERN = r'|'.join([
    *DETERMINATIVE_OR_GLOSS.values(),
    JOINER,
    DIVIDER
])


BRACES_PATTERN = (
    r'(?<![^\s])'
    r'\(([^\(\)]*)\)'
    r'(?!=[^\s])'
)


def _clean_line(line: str) -> str:
    return (
        pydash
        .chain(line)
        .reg_exp_replace(WHITE_SPACE_PATTERN, ' ')
        .reg_exp_replace(STRIP_PATTERN, '')
        .reg_exp_replace(BRACES_PATTERN, r'\1')
        .clean()
        .value()
    )


def _clean_values(line: str) -> str:
    return (
        pydash
        .chain(line)
        .split(' ')
        .map(_clean_value)
        .join(' ')
        .clean()
        .value()
    )


def _clean_value(value: str) -> str:
    grapheme = re.fullmatch(r'\|[^|]+\|', value)
    reading_with_sign = re.fullmatch(r'[^(]+\(([^)]+)\)', value)
    if VARIANT_SEPARATOR in value:
        return _clean_variant(value)
    elif grapheme or reading_with_sign:
        return value
    else:
        return _clean_reading(value)


def _clean_variant(value: str) -> str:
    return VARIANT_SEPARATOR.join([
        _clean_value(part)
        for part in value.split(VARIANT_SEPARATOR)
    ])


def _clean_reading(value: str) -> str:
    return (
        pydash.chain(value)
        .reg_exp_replace(r'[.+]', ' ')
        .reg_exp_replace(r'@[^\s]+', '')
        .value()
        .lower()
    )


@attr.s(frozen=True, auto_attribs=True)
class CleanAtf:
    atf: Atf

    @property
    def cleaned(self) -> List[str]:
        return (
            pydash
            .chain(self.filtered)
            .map(_clean_line)
            .map(_clean_values)
            .value()
        )

    @property
    def filtered(self) -> List[str]:
        return [
            line
            for line in self.atf.split('\n')
            if line and not re.match(IGNORE_LINE_PATTERN, line)
        ]

    @property
    def values(self) -> Sequence[Sequence[Value]]:
        return (
            pydash
            .chain(self.cleaned)
            .map(lambda row: [
                parse_reading(value)
                for value in row.split(WORD_SEPARATOR)
            ])
            .value()
        )
