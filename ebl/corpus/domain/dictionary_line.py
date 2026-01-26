import attr
from typing import Sequence
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.text_id import TextId
from ebl.common.domain.stage import Stage
import ebl.corpus.domain.chapter_validators as validators


@attr.s(auto_attribs=True, frozen=True)
class DictionaryLine:
    text_id: TextId
    text_name: str
    chapter_name: str
    stage: Stage
    line: Line
    manuscripts: Sequence[Manuscript] = attr.ib(
        default=(),
        validator=[
            validators.validate_manuscript_ids,
            validators.validate_manuscript_sigla,
        ],
    )


@attr.s(auto_attribs=True, frozen=True)
class DictionaryLinePagination:
    dictionary_lines: Sequence[DictionaryLine]
    total_count: int
