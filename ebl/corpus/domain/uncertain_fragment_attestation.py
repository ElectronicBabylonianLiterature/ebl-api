import attr
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.corpus.domain.text import Text
from ebl.corpus.domain.chapter import ChapterId


@attr.s(auto_attribs=True, frozen=True)
class UncertainFragmentAttestation:
    museum_number: MuseumNumber
    text: Text
    chapter_id: ChapterId
