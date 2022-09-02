import attr
from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.text_id import TextId


@attr.s(auto_attribs=True, frozen=True)
class DictionaryLine:
    text_id: TextId
    text_name: str
    chapter_name: str
    line: Line
