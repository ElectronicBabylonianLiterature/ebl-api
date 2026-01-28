from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import Sequence, TypeVar

import attr

from ebl.errors import NotFoundError
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_id import TextId

T = TypeVar("T", bound=Line)


class ParallelRepository(ABC):
    @abstractmethod
    def fragment_exists(self, museum_number: MuseumNumber) -> bool: ...

    @abstractmethod
    def find_implicit_chapter(self, text_id: TextId) -> ChapterName: ...

    @abstractmethod
    def chapter_exists(self, text_id: TextId, chapter_name: ChapterName) -> bool: ...


class ParallelLineInjector:
    _repository: ParallelRepository

    def __init__(self, repository: ParallelRepository):
        self._repository = repository

    def inject(self, lines: Sequence[T]) -> Sequence[T]:
        return tuple(self._inject_line(line) for line in lines)

    def inject_transliteration(self, transliteration: Text) -> Text:
        return attr.evolve(transliteration, lines=self.inject(transliteration.lines))

    @singledispatchmethod
    def _inject_line(self, line: T) -> T:
        return line

    @_inject_line.register(ParallelFragment)
    def _(self, line: ParallelFragment) -> ParallelFragment:
        return attr.evolve(
            line,
            exists=self._repository.fragment_exists(line.museum_number),
        )

    @_inject_line.register(ParallelText)
    def _(self, line: ParallelText) -> ParallelText:
        try:
            return (
                attr.evolve(
                    line,
                    exists=True,
                    implicit_chapter=self._repository.find_implicit_chapter(line.text),
                )
                if line.chapter is None
                else attr.evolve(
                    line,
                    exists=self._repository.chapter_exists(line.text, line.chapter),
                )
            )
        except NotFoundError:
            return attr.evolve(line, exists=False)
