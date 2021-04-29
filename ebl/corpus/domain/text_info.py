from typing import Mapping, Sequence

import attr

from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript import Siglum
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text import Text
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


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
        matching_lines = chapter.get_matching_lines(query)
        matching_colophon_lines = chapter.get_matching_colophon_lines(query)

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
