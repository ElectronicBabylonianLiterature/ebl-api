import re
from itertools import chain
from typing import Sequence, Tuple

import attr


def get_line_number(signs: str, position: int) -> int:
    return len([char for char in chain.from_iterable(signs[:position]) if char == "\n"])


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQuery:
    _signs: Sequence[Sequence[str]]
    regexp: str

    def is_empty(self) -> bool:
        return "".join(token for row in self._signs for token in row).strip() == ""

    def match(self, signs: str) -> Sequence[Tuple[int, int]]:
        return [
            (get_line_number(signs, match.start()), get_line_number(signs, match.end()))
            for match in re.finditer(self.regexp, signs)
        ]
