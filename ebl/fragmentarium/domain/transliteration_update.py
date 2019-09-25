from typing import Optional

import attr

from ebl.atf.domain.atf import Atf, AtfSyntaxError, validate_atf
from ebl.atf.domain.clean_atf import CleanAtf
from ebl.transliteration.domain.atf_parser import parse_atf
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import \
    TransliterationError


@attr.s(auto_attribs=True, frozen=True)
class TransliterationUpdate:
    atf: Atf = attr.ib(default=Atf(''))
    notes: str = ''
    signs: Optional[str] = attr.ib(default=None)

    def parse(self) -> Text:
        return parse_atf(self.atf)

    @atf.validator
    def _check_atf(self, _attribute, value):
        try:
            validate_atf(value)
        except AtfSyntaxError as error:
            raise TransliterationError([{
                'description': 'Invalid line',
                'lineNumber': error.line_number
            }])

    @signs.validator
    def _check_signs(self, _attribute, value):
        clean_atf = CleanAtf(self.atf)
        lines = clean_atf.atf.split('\n')

        def get_line_number(filtered_line_number):
            line = clean_atf.filtered[filtered_line_number]
            return lines.index(line) + 1

        if value is not None:
            signs = value.split('\n')
            questionable_lines = [
                get_line_number(index)
                for index, line in enumerate(signs)
                if '?' in line
            ]
            if questionable_lines:
                raise TransliterationError([{
                    'description': 'Invalid value',
                    'lineNumber': line_number
                } for line_number in questionable_lines])
