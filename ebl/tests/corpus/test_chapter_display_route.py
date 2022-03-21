import falcon
import pytest

from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.text import Text
from ebl.tests.corpus.support import create_chapter_url
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
    return create_chapter_url(chapter, "/display")


def test_get(client, text_repository, text, chapter, url):
    text_repository.create_many(text)
    text_repository.create_chapter(chapter)
    chapter_display = ChapterDisplay.of_chapter(text, chapter)

    get_result = client.simulate_get(url)

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == ChapterDisplaySchema().dump(chapter_display)


def test_text_not_found(client, text_repository, text, chapter, url):
    text_repository.create_many(text)

    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND


def test_chapter_not_found(client, text_repository, chapter, url):
    text_repository.create_chapter(chapter)

    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND
