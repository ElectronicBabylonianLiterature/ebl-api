from typing import List, Sequence, Tuple, Union

import attr

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
    matching_lines: Sequence[Sequence[Union[Line, TextLine]]]

    @staticmethod
    def of(chapter: Chapter, query: TransliterationQuery) -> "ChapterInfo":
        line_numbers: List[Sequence[Tuple[int, int]]] = [
            query.match(signs) for signs in chapter.signs
        ]
        text_lines: Sequence[Sequence[TextLineEntry]] = [
            chapter.get_manuscript_text_lines(manuscript)
            for manuscript in chapter.manuscripts
        ]
        matching_lines: List[List[Union[TextLine, Line]]] = [
            [
                line.source or line.line
                for start, end in numbers
                for line in text_lines[index][start:end]
            ]
            for index, numbers in enumerate(line_numbers)
        ]
        return ChapterInfo(
            ChapterId(chapter.classification, chapter.stage, chapter.name),
            matching_lines,
        )


@attr.s(auto_attribs=True, frozen=True)
class TextInfo:
    id_: TextId
    matching_chapters: Sequence[ChapterInfo]

    @staticmethod
    def of(text: Text, query: TransliterationQuery) -> "TextInfo":
        return TextInfo(
            text.id, [ChapterInfo.of(chapter, query) for chapter in text.chapters]
        )
