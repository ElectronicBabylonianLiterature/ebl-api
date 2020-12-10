from typing import List, Sequence

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter, Line, ManuscriptLine
from ebl.transliteration.domain.lemmatization import (
    LemmatizationToken,
    LemmatizationError,
)


class LemmatizationUpdater(ChapterUpdater):
    def __init__(
        self,
        chapter_index: int,
        lemmatization: Sequence[Sequence[Sequence[LemmatizationToken]]],
    ):
        super().__init__(chapter_index)
        self._lemmatization = lemmatization
        self._lines: List[Line] = []
        self._manuscript_lines: List[ManuscriptLine] = []

    @property
    def line_index(self) -> int:
        return len(self._lines)

    @property
    def manuscript_line_index(self) -> int:
        return len(self._manuscript_lines)

    @property
    def current_lemmatization(self) -> Sequence[LemmatizationToken]:
        try:
            return self._lemmatization[self.line_index][self.manuscript_line_index + 1]
        except IndexError:
            raise LemmatizationError(
                f"No lemmatization for line {self.line_index} "
                f"manuscript {self.manuscript_line_index}."
            )

    def visit_line(self, line: Line) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            if len(self._lemmatization[self.line_index]) == len(line.manuscripts) + 1:
                self._lines.append(
                    attr.evolve(
                        line,
                        text=line.text.update_lemmatization(
                            self._lemmatization[self.line_index][0]
                        ),
                        manuscripts=tuple(self._manuscript_lines),
                    )
                )
                self._manuscript_lines = []
            else:
                raise LemmatizationError()

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        if len(self._chapters) == self._chapter_index_to_align:
            updated_line = manuscript_line.line.update_lemmatization(
                self.current_lemmatization
            )
            self._manuscript_lines.append(
                attr.evolve(manuscript_line, line=updated_line)
            )

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        if len(self._lemmatization) == len(chapter.lines):
            return attr.evolve(chapter, lines=tuple(self._lines))
        else:
            raise LemmatizationError()

    def _after_chapter_update(self) -> None:
        self._lines = []
