from typing import Sequence

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.application.sign_repository import SignRepository


class ManuscriptUpdater(ChapterUpdater):
    def __init__(
        self,
        manuscripts: Sequence[Manuscript],
        uncertain_fragments: Sequence[MuseumNumber],
        sign_repository: SignRepository,
    ):
        super().__init__()
        self._manuscripts = manuscripts
        self._uncertain_fragments = uncertain_fragments
        self._sign_updater = SignsUpdater(sign_repository)

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return self._sign_updater.update(
            attr.evolve(
                chapter,
                manuscripts=self._manuscripts,
                uncertain_fragments=self._uncertain_fragments,
            )
        )
