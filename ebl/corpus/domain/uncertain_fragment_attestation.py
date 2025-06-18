import attr
from ebl.corpus.domain.text import Text
from ebl.corpus.domain.chapter import ChapterId


@attr.s(auto_attribs=True, frozen=True)
class UncertainFragmentAttestation:
    text: Text
    chapter_id: ChapterId
