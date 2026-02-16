import attr
from ebl.corpus.domain.text import Text
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.chapter import ChapterId


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptAttestation:
    text: Text
    chapter_id: ChapterId
    manuscript: Manuscript

    @property
    def manuscript_siglum(self) -> str:
        return str(self.manuscript.siglum)
