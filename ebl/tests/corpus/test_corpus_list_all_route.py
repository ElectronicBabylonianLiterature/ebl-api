import falcon
import pytest

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.text import Text
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


def test_list_all_texts_route(text, text_repository, client) -> None:
    text_repository.create(text)
    get_result = client.simulate_get("/corpus/texts/all")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [
        {"index": text.index, "category": text.category, "genre": text.genre.value}
    ]


def test_list_all_chapters_route(chapter, text, text_repository, client) -> None:
    text_repository.create_chapter(chapter)

    get_result = client.simulate_get("/corpus/chapters/all")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [
        {
            "chapter": chapter.name,
            "stage": chapter.stage.abbreviation,
            "index": text.index,
            "category": text.category,
            "genre": text.genre.value,
        }
    ]
