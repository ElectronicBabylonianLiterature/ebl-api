from typing import Sequence, Optional

import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.atf import WORD_SEPARATOR
from ebl.transliteration.domain.text import TextLine
from ebl.signs.infrastructure.memoizing_sign_repository import MemoizingSignRepository


class SignsUpdater:
    def __init__(self, sign_repository: SignRepository):
        self._sign_repository = MemoizingSignRepository(sign_repository)

    def update(self, chapter: Chapter) -> Chapter:
        return attr.evolve(chapter, signs=self._create_signs(chapter))

    def _create_signs(self, chapter: Chapter) -> Sequence[Optional[str]]:
        return tuple(
            self._map_lines([entry.line for entry in manuscript])
            for manuscript in chapter.text_lines
        )

    def _map_lines(self, lines: Sequence[TextLine]) -> Optional[str]:
        return "\n".join(self._map_line(line) for line in lines) if lines else None

    def _map_line(self, line: TextLine) -> str:
        visitor = SignsVisitor(self._sign_repository)
        line.accept(visitor)
        return WORD_SEPARATOR.join(visitor.result_string)
