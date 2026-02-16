from typing import Mapping, Sequence

import attr

from ebl.corpus.domain.manuscript import Siglum
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class ChapterInfo:
    id_: ChapterId
    text_name: str
    siglums: Mapping[int, Siglum]
    matching_lines: Sequence[Line]
    matching_colophon_lines: Mapping[int, Sequence[TextLine]]

    @staticmethod
    def of(chapter: Chapter, query: TransliterationQuery) -> "ChapterInfo":
        matching_lines = chapter.get_matching_lines(query)
        matching_colophon_lines = chapter.get_matching_colophon_lines(query)

        return ChapterInfo(
            chapter.id_,
            chapter.text_name,
            {manuscript.id: manuscript.siglum for manuscript in chapter.manuscripts},
            matching_lines,
            matching_colophon_lines,
        )


@attr.s(auto_attribs=True, frozen=True)
class ChapterInfosPagination:
    chapter_infos: Sequence[ChapterInfo]
    total_count: int
