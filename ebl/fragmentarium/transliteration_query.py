import re
import pydash

from ebl.fragmentarium.transliterations import filter_lines


class TransliterationQuery:
    def __init__(self, signs):
        self.signs = signs

    @property
    def regexp(self):
        lines_regexp = (
            pydash.chain(self.signs)
            .map(lambda row: [re.escape(sign) for sign in row])
            .map(' '.join)
            .map(lambda row: fr'(?<![^ |\n]){row}')
            .join(r'( .*)?\n.*')
            .value()
        )
        return fr'{lines_regexp}(?![^ |\n])'

    def get_matching_lines(self, fragment):
        signs = fragment['signs']
        transliteration = fragment['transliteration']

        def _line_number(position):
            return (
                pydash.chain(signs[:position])
                .chars()
                .filter_(lambda char: char == '\n')
                .size()
                .value()
            )

        matches = re.finditer(self.regexp, signs)
        positions = [
            (match.start(), match.end())
            for match in matches
        ]
        line_numbers = [
            (_line_number(position[0]), _line_number(position[1]))
            for position in positions
        ]

        lines = filter_lines(transliteration)

        return [
            lines[numbers[0]:numbers[1]+1]
            for numbers in pydash.uniq(line_numbers)
        ]
