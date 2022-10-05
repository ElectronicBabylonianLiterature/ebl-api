from typing import cast

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_info import ChapterInfo
from ebl.corpus.web.chapter_info_schema import ChapterInfoSchema, ChapterInfoLineSchema
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery

CHAPTER: Chapter = ChapterFactory.build()
QUERY = TransliterationQuery([["KU"]])
CHAPTER_INFO = ChapterInfo.of(CHAPTER, QUERY)


def test_of() -> None:
    assert CHAPTER_INFO == ChapterInfo(
        CHAPTER.id_,
        CHAPTER.text_name,
        {CHAPTER.manuscripts[0].id: CHAPTER.manuscripts[0].siglum},
        [CHAPTER.lines[0]],
        {
            CHAPTER.manuscripts[0].id: [
                cast(TextLine, CHAPTER.manuscripts[0].colophon.lines[0])
            ]
        },
    )


def test_chapter_info_schema() -> None:
    dump = ChapterInfoSchema().dump(CHAPTER_INFO)
    assert dump["id"] == ChapterIdSchema().dump(CHAPTER_INFO.id_)
    assert dump["textName"] == ""
    assert dump["siglums"] == {str(k): str(v) for k, v in CHAPTER_INFO.siglums.items()}
    assert dump["matchingLines"] == ChapterInfoLineSchema(many=True).dump(
        CHAPTER_INFO.matching_lines
    )
    assert dump["matchingColophonLines"] == {
        str(k): TextLineSchema(many=True).dump(v)
        for k, v in CHAPTER_INFO.matching_colophon_lines.items()
    }
