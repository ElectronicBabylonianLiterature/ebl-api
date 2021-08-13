import falcon

from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory
from ebl.tests.corpus.support import create_chapter_url
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.text import Text


def test_get(client, text_repository):
    chapter = ChapterFactory.build(
        lines=tuple(),
        manuscripts=(
            ManuscriptFactory.build(references=tuple()),
            ManuscriptFactory.build(unplaced_lines=Text(), references=tuple()),
            ManuscriptFactory.build(references=tuple()),
        ),
    )
    text_repository.create_chapter(chapter)

    result = client.simulate_get(create_chapter_url(chapter, "/unplaced_lines"))

    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.json == [
        {
            "siglum": str(manuscript.siglum),
            "text": TextSchema().dump(manuscript.unplaced_lines),
        }
        for manuscript in chapter.manuscripts
        if not manuscript.unplaced_lines.is_empty
    ]
