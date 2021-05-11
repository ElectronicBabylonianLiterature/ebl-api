from typing import cast

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_info import ChapterInfo
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


def test_of() -> None:
    chapter: Chapter = ChapterFactory.build()
    query = TransliterationQuery([["KU"]])
    assert ChapterInfo.of(chapter, query) == ChapterInfo(
        chapter.id_,
        {chapter.manuscripts[0].id: chapter.manuscripts[0].siglum},
        [chapter.lines[0]],
        {
            chapter.manuscripts[0].id: [
                cast(TextLine, chapter.manuscripts[0].colophon.lines[0])
            ]
        },
    )
