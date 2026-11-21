from abc import abstractmethod
from typing import Sequence, Type

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.errors import DataError


def require_count(
    error_class: Type[Exception], subject: str, got: int, expected: int
) -> None:
    if got != expected:
        raise error_class(
            f"Invalid number of {subject}. Got {got}, expected {expected}."
        )


def require_manuscript_token_counts(
    error_class: Type[Exception], line: Line, token_counts: Sequence[Sequence[int]]
) -> None:
    require_count(error_class, "variants", len(token_counts), len(line.variants))
    for variant_index, variant in enumerate(line.variants):
        manuscript_counts = token_counts[variant_index]
        require_count(
            error_class,
            f"manuscripts in variant {variant_index}",
            len(manuscript_counts),
            len(variant.manuscripts),
        )
        for manuscript_index, manuscript_line in enumerate(variant.manuscripts):
            require_count(
                error_class,
                f"tokens in variant {variant_index} manuscript {manuscript_index}",
                manuscript_counts[manuscript_index],
                len(manuscript_line.get_line_content()),
            )


class EachLineUpdater(ChapterUpdater):
    def __init__(self) -> None:
        super().__init__()
        self._lines: Sequence[Line] = ()

    @abstractmethod
    def _update_line(self, index: int, line: Line) -> Line:
        return line

    def _visit_lines(self, chapter: Chapter) -> None:
        self._lines = tuple(
            self._update_line(index, line) for index, line in enumerate(chapter.lines)
        )

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return attr.evolve(chapter, lines=self._lines)


class LineUpdater(ChapterUpdater):
    def __init__(self, index: int) -> None:
        super().__init__()
        self._index = index

    @abstractmethod
    def _update_line(self, line: Line) -> Line:
        return line

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        line_count = len(chapter.lines)
        if not 0 <= self._index < line_count:
            raise DataError(
                f"Invalid line: {self._index} is not a line position "
                f"(number of lines: {line_count})."
            )
        return attr.evolve(
            chapter,
            lines=tuple(
                self._update_line(line) if index == self._index else line
                for index, line in enumerate(chapter.lines)
            ),
        )
