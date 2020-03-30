from typing import Sequence
from itertools import chain

import attr
import pydash
import regex

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import Lines
from ebl.transliteration.domain.clean_atf import CleanAtf


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQuery:
    _signs: Sequence[Sequence[str]]

    @property
    def regexp(self):
        lines_regexp = map(
            lambda row: " ".join([
                fr"([^\s]+/)*{escaped_sign}(/[^\s]+)*"
                for escaped_sign in (regex.escape(sign) for sign in row)
            ]),
            self._signs
        )
        lines_regexp = r"( .*)?\n.*".join(map(lambda row: fr"(?<![^|\s]){row}",
                                              lines_regexp))
        return fr"{lines_regexp}(?![^|\s])"

    def is_empty(self) -> bool:
        return "".join(token for row in self._signs for token in row).strip() == ""

    def get_matching_lines(self, fragment: Fragment) -> Lines:
        signs = fragment.signs

        def line_number(position):
            return len([char for char
                       in chain.from_iterable(signs[:position])
                       if char == "\n"])

        matches = regex.finditer(self.regexp, signs, overlapped=True)
        positions = [(match.start(), match.end()) for match in matches]
        line_numbers = [
            (line_number(position[0]), line_number(position[1]))
            for position in positions
        ]

        lines = CleanAtf(fragment.text.atf).filtered

        return tuple(
            tuple(lines[numbers[0] : numbers[1] + 1])
            for numbers in pydash.uniq(line_numbers)
        )
