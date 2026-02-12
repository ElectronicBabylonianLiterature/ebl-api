import attr
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.line import Line
from ebl.corpus.web.display_schemas import LineDetailsDisplay
from ebl.common.domain.stage import Stage

from ebl.transliteration.domain.text_id import TextId


@attr.s(frozen=True, auto_attribs=True)
class DictionaryLineDisplay:
    text_id: TextId
    text_name: str
    chapter_name: str
    stage: Stage
    line: Line
    line_details: LineDetailsDisplay

    @classmethod
    def from_dictionary_line(
        cls, dictionary_line: DictionaryLine
    ) -> "DictionaryLineDisplay":
        return cls(
            dictionary_line.text_id,
            dictionary_line.text_name,
            dictionary_line.chapter_name,
            dictionary_line.stage,
            dictionary_line.line,
            LineDetailsDisplay.from_line_manuscripts(
                dictionary_line.line, dictionary_line.manuscripts
            ),
        )
