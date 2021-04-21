from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.text_info import ChapterId, ChapterInfo
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from typing import cast
from ebl.transliteration.domain.text_line import TextLine


def test_of() -> None:
    chapter: Chapter = ChapterFactory.build()
    query = TransliterationQuery([["KU"]])
    assert ChapterInfo.of(chapter, query) == ChapterInfo(
        ChapterId(chapter.classification, chapter.stage, chapter.name),
        {chapter.manuscripts[0].id: chapter.manuscripts[0].siglum},
        [chapter.lines[0]],
        {
            chapter.manuscripts[0].id: [
                cast(TextLine, chapter.manuscripts[0].colophon.lines[0])
            ]
        },
    )
