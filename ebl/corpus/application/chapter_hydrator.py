from functools import singledispatchmethod
from typing import cast, Iterable, List, Optional, Sequence

import attr

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.chapter import Chapter, ChapterItem, ChapterVisitor
from ebl.corpus.domain.manuscript import Manuscript
from ebl.errors import Defect


class ChapterHydartor(ChapterVisitor):
    def __init__(self, bibliography: Bibliography):
        self._bibliography: Bibliography = bibliography
        self._chapter: Optional[Chapter] = None
        self._manuscripts: List[Manuscript] = []

    @property
    def chapter(self) -> Chapter:
        if self._chapter is None:
            raise Defect("Trying to access chapter before a chapter was visited.")
        else:
            return cast(Chapter, self._chapter)

    @singledispatchmethod
    def visit(self, item: ChapterItem) -> None:
        pass

    @visit.register(Chapter)
    def _visit_chapter(self, chapter: Chapter) -> None:
        for manuscript in chapter.manuscripts:
            self.visit(manuscript)

        self._chapter = attr.evolve(chapter, manuscripts=tuple(self._manuscripts))
        self._manuscripts = []

    @visit.register(Manuscript)
    def _visit_manuscript(self, manuscript: Manuscript) -> None:
        self._manuscripts.append(self.hydrate_manuscript(manuscript))

    def hydrate_manuscript(self, manuscript: Manuscript) -> Manuscript:
        references = self._hydrate_references(manuscript.references)
        return attr.evolve(manuscript, references=references)

    def _hydrate_references(
        self, references: Iterable[Reference]
    ) -> Sequence[Reference]:
        return tuple(self._hydrate_reference(reference) for reference in references)

    def _hydrate_reference(self, reference: Reference) -> Reference:
        document = self._bibliography.find(reference.id)
        return attr.evolve(reference, document=document)
