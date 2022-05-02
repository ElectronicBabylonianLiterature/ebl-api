import falcon

from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory
from ebl.tests.corpus.support import create_chapter_url
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.text import Text


def test_get(client, text_repository):
    chapter = ChapterFactory.build(
        lines=tuple(),
        manuscripts=(
            ManuscriptFactory.build(references=tuple(), old_sigla=tuple()),
            ManuscriptFactory.build(
                colophon=Text(), references=tuple(), old_sigla=tuple()
            ),
            ManuscriptFactory.build(references=tuple(), old_sigla=tuple()),
        ),
    )
    text_repository.create_chapter(chapter)

    result = client.simulate_get(create_chapter_url(chapter, "/colophons"))

    assert result.status == falcon.HTTP_OK
    assert result.json == [
        {
            "siglum": str(manuscript.siglum),
            "text": TextSchema().dump(manuscript.colophon),
        }
        for manuscript in chapter.manuscripts
        if not manuscript.colophon.is_empty
    ]
