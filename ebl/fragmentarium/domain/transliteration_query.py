import re
from itertools import chain, groupby
from typing import Sequence

import attr

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import Lines


def create_sign_regexp(sign):
    return fr"([^\s]+\/)*{re.escape(sign)}(\/[^\s]+)*"


def create_line_regexp(line):
    signs_regexp = " ".join(create_sign_regexp(sign) for sign in line)
    return fr"(?<![^|\s]){signs_regexp}"


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQuery:
    _signs: Sequence[Sequence[str]]

    @property
    def regexp(self):
        lines_regexp = r"( .*)?\n.*".join(
            create_line_regexp(line) for line in self._signs
        )

        return fr"{lines_regexp}(?![^|\s])"

    def is_empty(self) -> bool:
        return "".join(token for row in self._signs for token in row).strip() == ""

    def get_matching_lines(self, fragment: Fragment) -> Lines:
        signs = fragment.signs

        def line_number(position):
            return len(
                [char for char in chain.from_iterable(signs[:position]) if char == "\n"]
            )

        matches = re.finditer(self.regexp, signs)
        line_numbers = [
            (line_number(match.start()), line_number(match.end())) for match in matches
        ]

        lines = [line.atf for line in fragment.text.text_lines]

        return tuple(
            tuple(lines[numbers[0] : numbers[1] + 1])
            for numbers, _ in groupby(line_numbers)
        )
