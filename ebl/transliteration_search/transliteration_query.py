import attr
import pydash
import regex

from ebl.atf.clean_atf import CleanAtf


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQuery:
    _signs: list

    @property
    def regexp(self):
        lines_regexp = (
            pydash.chain(self._signs)
            .map(lambda row: [
                fr'([^\s]+/)*{escaped_sign}(/[^\s]+)*'
                for escaped_sign
                in (regex.escape(sign) for sign in row)
            ])
            .map(' '.join)
            .map(lambda row: fr'(?<![^|\s]){row}')
            .join(r'( .*)?\n.*')
            .value()
        )
        return fr'{lines_regexp}(?![^|\s])'

    def get_matching_lines(self, transliteration):
        signs = transliteration.signs

        def line_number(position):
            return (
                pydash.chain(signs[:position])
                .chars()
                .filter_(lambda char: char == '\n')
                .size()
                .value()
            )

        matches = regex.finditer(self.regexp, signs, overlapped=True)
        positions = [
            (match.start(), match.end())
            for match in matches
        ]
        line_numbers = [
            (line_number(position[0]), line_number(position[1]))
            for position in positions
        ]

        lines = CleanAtf(transliteration.atf).filtered

        return [
            lines[numbers[0]:numbers[1] + 1]
            for numbers in pydash.uniq(line_numbers)
        ]
