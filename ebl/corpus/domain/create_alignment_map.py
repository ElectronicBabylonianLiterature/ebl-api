import difflib
from typing import Callable, Sequence

import pydash

from ebl.transliteration.domain.text_line import AlignmentMap
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord

UNCHANGED: str = " "
REMOVED: str = "-"
ADDED: str = "+"


class Mapper:
    def __init__(self, old: Sequence[Token], new: Sequence[Token]) -> None:
        self._new = new
        self._diff = difflib.ndiff(
            [token.value for token in old], [token.value for token in new]
        )
        self._alignment = 0
        self._removals = 0
        self._result = []

    def map_(self) -> AlignmentMap:
        self._alignment = 0
        self._removals = 0
        self._result = []

        for delta in self._diff:
            self._get_method(delta)()

        return self._result

    def _get_method(self, delta: str) -> Callable[[], None]:
        return {UNCHANGED: self._keep, REMOVED: self._remove, ADDED: self._add}.get(
            delta[:1], pydash.noop
        )

    def _keep(self) -> None:
        self._result.append(self._alignment)
        self._alignment += 1
        self._removals = 0

    def _remove(self) -> None:
        self._result.append(None)
        self._removals += 1

    def _add(self) -> None:
        if self._removals > 0:
            self._result[-self._removals] = (
                self._alignment
                if isinstance(self._new[self._alignment], AbstractWord)
                else None
            )
            self._removals -= 1
        self._alignment += 1


def create_alignment_map(old: Sequence[Token], new: Sequence[Token]) -> AlignmentMap:
    return Mapper(old, new).map_()
