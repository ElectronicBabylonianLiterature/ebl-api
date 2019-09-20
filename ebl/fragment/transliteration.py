import re
from typing import List, Optional, Sequence

import attr
import pydash

from ebl.text.atf import ATF_EXTENSIONS, ATF_SPEC, Atf
from ebl.text.atf_parser import parse_atf
from ebl.text.text import Text
from ebl.transliteration_search.value import Value
from ebl.transliteration_search.value_mapper import parse_reading

IGNORE_LINE_PATTERN = r'|'.join([
    ATF_SPEC['control_line'],
    ATF_SPEC['multiplex_comment']
])
STRIP_PATTERN = r'|'.join([
    ATF_EXTENSIONS['erasure_illegible'],
    ATF_EXTENSIONS['erasure_boundary'],
    *ATF_SPEC['flags'].values(),
    *ATF_SPEC['lacuna'].values(),
    f'{ATF_SPEC["line_number"]}\\s+',
    ATF_SPEC['removal'],
    ATF_SPEC['omission'],
    ATF_SPEC['tabulation'],
    f'{ATF_SPEC["shift"]}\\s+',
    ATF_EXTENSIONS['line_continuation'],
    ATF_SPEC['alternative_damage']
])
WHITE_SPACE_PATTERN = r'|'.join([
    *ATF_SPEC['determinative_or_gloss'].values(),
    ATF_SPEC['joiner'],
    ATF_SPEC['divider']
])
BRACES_PATTERN = (
    r'(?<![^\s])'
    r'\(([^\(\)]*)\)'
    r'(?!=[^\s])'
)
VARIANT_SEPARATOR = ATF_SPEC['variant_separator']


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


@attr.s(auto_attribs=True, frozen=True)
class Transliteration:
    atf: Atf = Atf('')
    notes: str = ''
    signs: Optional[str] = None

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

    def with_signs(self, transliteration_search) -> 'Transliteration':
        signs = '\n'.join([
            ' '.join(row)
            for row in transliteration_search.map_readings(self.values)
        ])
        return attr.evolve(self, signs=signs)

    @property
    def values(self) -> Sequence[Sequence[Value]]:
        return (
            pydash
            .chain(self.cleaned)
            .map(lambda row: [
                parse_reading(value)
                for value in row.split(ATF_SPEC['word_separator'])
            ])
            .value()
        )

    def parse(self) -> Text:
        return parse_atf(self.atf)
