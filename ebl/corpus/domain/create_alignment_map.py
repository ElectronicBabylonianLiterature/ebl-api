from typing import Iterable

import difflib

from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.text_line import AlignmentMap

UNCHANGED: str = " "
REMOVED: str = "-"
ADDED: str = "+"


def create_alignment_map(old: Iterable[Token], new: Iterable[Token]) -> AlignmentMap:
    diff = difflib.ndiff([token.value for token in old], [token.value for token in new])
    alignment = 0
    removals = 0
    result = []

    for delta in diff:
        if delta.startswith(UNCHANGED):
            result.append(alignment)
            alignment += 1
            removals = 0
        elif delta.startswith(REMOVED):
            result.append(None)
            removals += 1
        elif delta.startswith(ADDED):
            if removals > 0:
                result[-removals] = alignment
                removals -= 1
            alignment += 1

    return result
