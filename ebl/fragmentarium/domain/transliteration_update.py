from typing import List, Optional

import attr

from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class TransliterationUpdate:
    text: Text = Text()
    notes: str = ""
    signs: Optional[str] = attr.ib(default=None)

    @signs.validator
    def _check_signs(self, _attribute, value) -> None:
        if value is not None:
            questionable_lines = self._get_questionable_lines(value)
            if questionable_lines:
                raise TransliterationError(
                    [
                        {"description": "Invalid value", "lineNumber": line_number,}
                        for line_number in questionable_lines
                    ]
                )

    def _get_questionable_lines(self, value: str) -> List[int]:
        lines = [line.atf for line in self.text.lines]
        text_lines = [
            line.atf
            for line in self.text.lines
            if isinstance(line, TextLine)
        ]
        signs = value.split("\n")

        def get_line_number(text_line_number: int) -> int:
            line = text_lines[text_line_number]
            return lines.index(line) + 1

        return [
            get_line_number(index)
            for index, line in enumerate(signs)
            if "?" in line
        ]
