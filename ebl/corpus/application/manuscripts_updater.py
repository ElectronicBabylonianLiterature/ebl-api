from typing import Sequence

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.manuscript import Manuscript
from ebl.fragmentarium.domain.museum_number import MuseumNumber


class ManuscriptUpdater(ChapterUpdater):
    def __init__(
        self,
        chapter_index: int,
        manuscripts: Sequence[Manuscript],
        uncertain_fragments: Sequence[MuseumNumber],
    ):
        super().__init__(chapter_index)
        self._manuscripts = manuscripts
        self._uncertain_fragments = uncertain_fragments

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return attr.evolve(
            chapter,
            manuscripts=self._manuscripts,
            uncertain_fragments=self._uncertain_fragments,
        )
