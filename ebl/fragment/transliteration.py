from typing import Optional

import attr

from ebl.text.atf import Atf, AtfSyntaxError, validate_atf
from ebl.text.atf_parser import parse_atf
from ebl.text.text import Text
from ebl.text.transliteration_error import TransliterationError
from ebl.transliteration_search.clean_atf import CleanAtf


@attr.s(auto_attribs=True, frozen=True)
class Transliteration:
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
