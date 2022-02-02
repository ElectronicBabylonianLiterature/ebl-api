import falcon
import pytest

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.text import Text
from ebl.corpus.web.display_schemas import LineDetailsSchema
from ebl.tests.corpus.support import create_chapter_url, allow_references
from ebl.tests.factories.corpus import ChapterFactory, TextFactory


@pytest.fixture
def chapter() -> Chapter:
    return ChapterFactory.build()


@pytest.fixture
def text(chapter: Chapter) -> Text:
    return TextFactory.build(
        genre=chapter.text_id.genre,
        category=chapter.text_id.category,
        index=chapter.text_id.index,
    )


@pytest.fixture
def url(chapter: Chapter) -> str:
    return create_chapter_url(chapter, "/lines")


def test_get(client, text_repository, text, chapter, bibliography, url):
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    allow_references(chapter, bibliography)
    schema = LineDetailsSchema(context={"manuscripts": chapter.manuscripts})

    get_result = client.simulate_get(f"{url}/0")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == schema.dump(chapter.lines[0])


def test_chapter_not_found(client, text_repository, text, chapter, url):
    text_repository.create(text)

    result = client.simulate_get(f"{url}/0")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_line_not_found(client, text_repository, chapter, bibliography, url):
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    allow_references(chapter, bibliography)

    result = client.simulate_get(f"{url}/{len(chapter.lines)}")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_line(client, text_repository, chapter, bibliography, url):
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    allow_references(chapter, bibliography)

    result = client.simulate_get(f"{url}/invalid")

    assert result.status == falcon.HTTP_NOT_FOUND
