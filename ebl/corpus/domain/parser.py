from typing import Iterable, Optional, Sequence, Union

from ebl.corpus.domain.chapter_transformer import ChapterTransformer
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript import Manuscript
from ebl.errors import DataError
from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.atf_parsers.lark_parser import CHAPTER_PARSER
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.note_line import NoteLine


def parse_chapter(
    atf: str, manuscripts: Iterable[Manuscript], start: Optional[str] = None
) -> Sequence[Line]:
    try:
        tree = CHAPTER_PARSER.parse(atf, start=start)
        return ChapterTransformer(manuscripts).transform(tree)
    except PARSE_ERRORS as error:
        raise DataError(error) from error


def parse_paratext(atf: str) -> Union[NoteLine, DollarLine]:
    tree = CHAPTER_PARSER.parse(atf, start="paratext")
    return ChapterTransformer(tuple()).transform(tree)
