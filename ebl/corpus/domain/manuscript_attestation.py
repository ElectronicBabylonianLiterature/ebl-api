from ebl.corpus.domain.text import ChapterListing, Text
from ebl.corpus.domain.manuscript import Manuscript, Siglum
from ebl.corpus.domain.chapter import ChapterId


class ManuscriptAttestation:
    text: Text
    chapter_id: ChapterId
    manuscript: Manuscript

    @property
    def siglum(self) -> Siglum:
        return self.manuscript.siglum
