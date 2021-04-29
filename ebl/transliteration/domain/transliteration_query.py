from itertools import chain
import re
from typing import Sequence, Tuple

import attr


def create_sign_regexp(sign):
    return fr"([^\s]+\/)*{re.escape(sign)}(\/[^\s]+)*"


def create_line_regexp(line):
    signs_regexp = " ".join(create_sign_regexp(sign) for sign in line)
    return fr"(?<![^|\s]){signs_regexp}"


def get_line_number(signs: str, position: int) -> int:
    return len([char for char in chain.from_iterable(signs[:position]) if char == "\n"])


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQuery:
    _signs: Sequence[Sequence[str]]

    @property
    def regexp(self) -> str:
        lines_regexp = r"( .*)?\n.*".join(
            create_line_regexp(line) for line in self._signs
        )

        return fr"{lines_regexp}(?![^|\s])"

    def is_empty(self) -> bool:
        return "".join(token for row in self._signs for token in row).strip() == ""

    def match(self, signs: str) -> Sequence[Tuple[int, int]]:
        return [
            (get_line_number(signs, match.start()), get_line_number(signs, match.end()))
            for match in re.finditer(self.regexp, signs)
        ]
