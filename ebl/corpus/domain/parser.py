from typing import Iterable, Optional, Sequence

from ebl.corpus.domain.chapter import Line
from ebl.corpus.domain.chapter_transformer import ChapterTransformer
from ebl.corpus.domain.manuscript import Manuscript
from ebl.errors import DataError
from ebl.transliteration.domain.lark_parser import CHAPTER_PARSER, PARSE_ERRORS


def parse_chapter(
    atf: str, manuscripts: Iterable[Manuscript], start: Optional[str] = None
) -> Sequence[Line]:
    try:
        tree = CHAPTER_PARSER.parse(atf, start=start)
        return ChapterTransformer(manuscripts).transform(tree)
    except PARSE_ERRORS as error:
        raise DataError(error) from error
