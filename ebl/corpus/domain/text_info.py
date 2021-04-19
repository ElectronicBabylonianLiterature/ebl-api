from typing import List, Mapping, Sequence, Tuple, cast

import attr
import pydash

from ebl.corpus.domain.manuscript import Siglum
from ebl.corpus.domain.text import Text
from ebl.corpus.domain.text_id import TextId
from ebl.corpus.domain.chapter import Chapter, Classification, Line, TextLineEntry
from ebl.corpus.domain.stage import Stage
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class ChapterId:
    classification: Classification
    stage: Stage
    name: str


@attr.s(auto_attribs=True, frozen=True)
class ChapterInfo:
    id_: ChapterId
    siglums: Mapping[int, Siglum]
    matching_lines: Sequence[Line]
    matching_colophon_lines: Mapping[int, Sequence[TextLine]]

    @staticmethod
    def of(chapter: Chapter, query: TransliterationQuery) -> "ChapterInfo":
        line_numbers: List[Sequence[Tuple[int, int]]] = [
            query.match(signs) for signs in chapter.signs
        ]
        text_lines: Sequence[Sequence[TextLineEntry]] = [
            chapter.get_manuscript_text_lines(manuscript)
            for manuscript in chapter.manuscripts
        ]

        matching_lines: List[Line] = [
            chapter.lines[index]
            for index in sorted(
                {
                    cast(int, line.source)
                    for index, numbers in enumerate(line_numbers)
                    for start, end in numbers
                    for line in text_lines[index][start : end + 1]
                    if line.source is not None
                }
            )
        ]
        matching_colophon_lines: Mapping[int, List[TextLine]] = pydash.omit_by(
            {
                chapter.manuscripts[index].id: [
                    line.line
                    for start, end in numbers
                    for line in text_lines[index][start : end + 1]
                    if line.source is None
                ]
                for index, numbers in enumerate(line_numbers)
            },
            pydash.is_empty,
        )

        return ChapterInfo(
            ChapterId(chapter.classification, chapter.stage, chapter.name),
            {manuscript.id: manuscript.siglum for manuscript in chapter.manuscripts},
            matching_lines,
            matching_colophon_lines,
        )


@attr.s(auto_attribs=True, frozen=True)
class TextInfo:
    id_: TextId
    matching_chapters: Sequence[ChapterInfo]

    @staticmethod
    def of(text: Text, query: TransliterationQuery) -> "TextInfo":
        return TextInfo(
            text.id,
            [
                chapter_info
                for chapter_info in [
                    ChapterInfo.of(chapter, query) for chapter in text.chapters
                ]
                if chapter_info.matching_lines or chapter_info.matching_colophon_lines
            ],
        )
