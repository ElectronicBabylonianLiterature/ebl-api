from typing import Tuple

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.text import Chapter, Manuscript


class ManuscriptUpdater(ChapterUpdater):

    def __init__(self, chapter_index: int,
                 manuscripts: Tuple[Manuscript, ...]):
        super().__init__(chapter_index)
        self._manuscripts = manuscripts

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return attr.evolve(chapter, manuscripts=self._manuscripts)
