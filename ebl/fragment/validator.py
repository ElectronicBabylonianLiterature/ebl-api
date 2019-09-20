from ebl.text.atf import AtfSyntaxError, validate_atf
from ebl.text.transliteration_error import TransliterationError
from ebl.transliteration_search.clean_atf import CleanAtf


class Validator:
    def __init__(self, transliteration):
        self._transliteration = transliteration

    def validate(self):
        errors = self.get_errors()
        if errors:
            raise TransliterationError(errors)

    def get_errors(self):
        return self._get_atf_errors() + self._get_value_errors()

    def _get_atf_errors(self):
        try:
            validate_atf(self._transliteration.atf)
            return []
        except AtfSyntaxError as error:
            return [{
                'description': 'Invalid line',
                'lineNumber': error.line_number
            }]

    def _get_value_errors(self):
        lines = self._transliteration.atf.split('\n')

        def get_line_number(filtered_line_number):
            line = CleanAtf(
                self._transliteration.atf
            ).filtered[filtered_line_number]
            return lines.index(line) + 1

        if self._transliteration.signs is not None:
            signs = self._transliteration.signs.split('\n')
            questionable_lines = [
                get_line_number(index)
                for index, line in enumerate(signs)
                if '?' in line
            ]
            return [{
                'description': 'Invalid value',
                'lineNumber': line_number
            } for line_number in questionable_lines]
        else:
            return []
