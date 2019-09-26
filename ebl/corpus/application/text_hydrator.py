from typing import Iterable, Tuple

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.text import Chapter, Manuscript, Text, TextVisitor
from ebl.errors import Defect, NotFoundError


def invalid_reference(error: Exception) -> Exception:
    return Defect(f'Invalid manuscript references: "{error}"')


class TextHydrator(TextVisitor):

    def __init__(self, bibliography):
        super().__init__(TextVisitor.Order.POST)
        self._bibliography = bibliography
        self.text = None
        self._chapters = []
        self._manuscripts = []

    def visit_text(self, text: Text) -> None:
        self.text = attr.evolve(text, chapters=tuple(self._chapters))
        self._chapters = []

    def visit_chapter(self, chapter: Chapter) -> None:
        self._chapters.append(
            attr.evolve(chapter, manuscripts=tuple(self._manuscripts))
        )
        self._manuscripts = []

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        references = self._hydrate_references(manuscript.references)
        self._manuscripts.append(attr.evolve(manuscript,
                                             references=references))

    def _hydrate_references(self, references: Iterable[Reference])\
            -> Tuple[Reference, ...]:
        return tuple(self._hydrate_reference(reference)
                     for reference in references)

    def _hydrate_reference(self, reference: Reference) -> Reference:
        try:
            document = self._bibliography.find(reference.id)
            return attr.evolve(reference, document=document)
        except NotFoundError as error:
            raise invalid_reference(error)
