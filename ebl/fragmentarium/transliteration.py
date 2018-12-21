import re
from typing import Optional, List, Callable, Any
import attr
import pydash
from ebl.atf import ATF_SPEC

IGNORE_LINE_PATTERN = r'|'.join([
    ATF_SPEC['control_line'],
    ATF_SPEC['multiplex_comment']
])
STRIP_PATTERN = r'|'.join([
    *ATF_SPEC['flags'].values(),
    *ATF_SPEC['lacuna'].values(),
    f'{ATF_SPEC["line_number"]}\\s+',
    ATF_SPEC['removal'],
    ATF_SPEC['omission'],
    ATF_SPEC['tabulation'],
    f'{ATF_SPEC["shift"]}\\s+',
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


class TransliterationError(Exception):
    def __init__(self, errors):
        super().__init__('Invalid transliteration')
        self.errors = errors


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
    reading_with_sign = re.fullmatch(r'[^\(]+\(([^\)]+)\)', value)
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
    atf: str
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

    def with_signs(self, sign_list) -> 'Transliteration':
        signs = '\n'.join([
            ' '.join(row)
            for row in self.to_sign_matrix(sign_list)
        ])
        return attr.evolve(self, signs=signs)

    def to_sign_matrix(self, sign_list) -> List[List[str]]:
        return sign_list.map_transliteration(self.cleaned)

    def tokenize(self, create_token: Callable[[str], Any]) -> List[List[Any]]:
        return [
            [
                create_token(value)
                for value in (
                    [line]
                    if re.match(IGNORE_LINE_PATTERN, line)
                    else line.split(ATF_SPEC['word_separator'])
                )
            ]
            for line in self.atf.split('\n')
        ] if self.atf else []
