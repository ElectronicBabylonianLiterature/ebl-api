from typing import Tuple

import attr

from ebl.corpus.chapter_updater import ChapterUpdater
from ebl.corpus.text import Chapter, Manuscript
from ebl.errors import DataError


class ManuscriptUpdater(ChapterUpdater):

    def __init__(self, chapter_index: int,
                 manuscripts: Tuple[Manuscript, ...]):
        super().__init__(chapter_index)
        self._manuscripts = manuscripts

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        try:
            return attr.evolve(chapter, manuscripts=self._manuscripts)
        except ValueError as error:
            raise DataError(error)
