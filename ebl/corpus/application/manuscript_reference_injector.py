from functools import singledispatchmethod
from typing import Iterable, List, Optional, Sequence

import attr

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.chapter import Chapter, ChapterItem, ChapterVisitor
from ebl.corpus.domain.manuscript import Manuscript, OldSiglum
from ebl.errors import Defect


class ManuscriptReferenceInjector(ChapterVisitor):
    def __init__(self, bibliography: Bibliography):
        self._bibliography: Bibliography = bibliography
        self._chapter: Optional[Chapter] = None
        self._manuscripts: List[Manuscript] = []

    @property
    def chapter(self) -> Chapter:
        if self._chapter is None:
            raise Defect("Trying to access chapter before a chapter was visited.")
        else:
            return self._chapter

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
        self._manuscripts.append(self.inject_manuscript(manuscript))

    def inject_manuscript(self, manuscript: Manuscript) -> Manuscript:
        references = self._inject_references(manuscript.references)
        old_sigla = self._inject_old_sigla(manuscript.old_sigla)
        return attr.evolve(manuscript, references=references, old_sigla=old_sigla)

    def _inject_references(
        self, references: Iterable[Reference]
    ) -> Sequence[Reference]:
        return tuple(self._inject_reference(reference) for reference in references)

    def _inject_reference(self, reference: Reference) -> Reference:
        document = self._bibliography.find(reference.id)
        return attr.evolve(reference, document=document)

    def _inject_old_sigla(self, old_sigla: Sequence[OldSiglum]) -> Sequence[OldSiglum]:
        return tuple(
            attr.evolve(
                old_siglum, reference=self._inject_reference(old_siglum.reference)
            )
            for old_siglum in old_sigla
        )
