from typing import cast

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_info import ChapterInfo
from ebl.corpus.web.chapter_info_schema import ChapterInfoSchema, ChapterInfoLineSchema
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.signs_visitor import SignsVisitor

CHAPTER: Chapter = ChapterFactory.build()


def test_of(sign_repository, signs) -> None:
    for sign in signs:
        sign_repository.create(sign)
    QUERY = TransliterationQuery(string="KU", visitor=SignsVisitor(sign_repository))
    CHAPTER_INFO = ChapterInfo.of(CHAPTER, QUERY)
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


def test_chapter_info_schema(sign_repository, signs) -> None:
    for sign in signs:
        sign_repository.create(sign)
    QUERY = TransliterationQuery(string="KU", visitor=SignsVisitor(sign_repository))
    CHAPTER_INFO = ChapterInfo.of(CHAPTER, QUERY)
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
