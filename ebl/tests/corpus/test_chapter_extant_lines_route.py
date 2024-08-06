import falcon

from ebl.corpus.web.extant_lines import ExtantLinesSchema
from ebl.tests.corpus.support import create_chapter_url
from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory


def test_get(client, text_repository):
    chapter = ChapterFactory.build(
        manuscripts=(ManuscriptFactory.build(id=1, references=()),)
    )
    text_repository.create_chapter(chapter)

    result = client.simulate_get(create_chapter_url(chapter, "/extant_lines"))

    assert result.status == falcon.HTTP_OK
    assert result.json == ExtantLinesSchema().dump(chapter)["extantLines"]
