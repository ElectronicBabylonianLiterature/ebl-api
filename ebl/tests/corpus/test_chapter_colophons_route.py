import falcon
import pytest

from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
)
from ebl.transliteration.application.text_schema import TextSchema


@pytest.mark.xfail
def test_get(client, bibliography, sign_repository, signs, text_repository):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build(manuscripts=tuple(
        ManuscriptFactory.build(),
        ManuscriptFactory.build(),
    ))
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    result = client.simulate_get(
        create_chapter_url(chapter, "/colophons")
    )

    result = client.simulate_get(create_chapter_url(chapter))

    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.json == create_chapter_dto([
        {
            "siglum": str(manuscript.siglum),
            "text": TextSchema().dump(manuscript.colophon)
        }
        for manuscript in chapter.manuscripts
    ])
