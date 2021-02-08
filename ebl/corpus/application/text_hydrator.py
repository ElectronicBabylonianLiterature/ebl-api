from typing import cast, Iterable, List, Optional, Sequence

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.text import Text, TextItem, TextVisitor
from ebl.errors import Defect, NotFoundError


def invalid_reference(error: Exception) -> Exception:
    return Defect(f'Invalid manuscript references: "{error}"')


class TextHydrator(TextVisitor):
    def __init__(self, bibliography: Bibliography):
        self._bibliography: Bibliography = bibliography
        self._text: Optional[Text] = None
        self._chapters: List[Chapter] = []
        self._manuscripts: List[Manuscript] = []

    @property
    def text(self) -> Text:
        if self._text is None:
            raise Defect("Trying to access text before a text was visited.")
        else:
            return cast(Text, self._text)

    @singledispatchmethod  # pyre-ignore[56]
    def visit(self, item: TextItem) -> None:
        pass

    @visit.register(Text)  # pyre-ignore[56]
    def _visit_text(self, text: Text) -> None:
        for chapter in text.chapters:
            self.visit(chapter)

        self._text = attr.evolve(text, chapters=tuple(self._chapters))
        self._chapters = []

    @visit.register(Chapter)  # pyre-ignore[56]
    def _visit_chapter(self, chapter: Chapter) -> None:
        for manuscript in chapter.manuscripts:
            self.visit(manuscript)

        self._chapters.append(
            attr.evolve(chapter, manuscripts=tuple(self._manuscripts))
        )
        self._manuscripts = []

    @visit.register(Manuscript)  # pyre-ignore[56]
    def _visit_manuscript(self, manuscript: Manuscript) -> None:
        references = self._hydrate_references(manuscript.references)
        self._manuscripts.append(attr.evolve(manuscript, references=references))

    def _hydrate_references(
        self, references: Iterable[Reference]
    ) -> Sequence[Reference]:
        return tuple(self._hydrate_reference(reference) for reference in references)

    def _hydrate_reference(self, reference: Reference) -> Reference:
        try:
            document = self._bibliography.find(reference.id)
            return attr.evolve(reference, document=document)
        except NotFoundError as error:
            raise invalid_reference(error)
