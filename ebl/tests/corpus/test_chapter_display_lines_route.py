from typing import Callable

import falcon
import pytest
from falcon import testing

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.manuscript_reference_injector import (
    ManuscriptReferenceInjector,
)

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.text import Text
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.web.display_schemas import LineDetailsDisplay, LineDetailsDisplaySchema
from ebl.tests.corpus.support import (
    allow_references,
    create_chapter_url,
    simulate_get,
)
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
def stored_chapter(
    text_repository: MongoTextRepository,
    text: Text,
    chapter: Chapter,
    bibliography: Bibliography,
) -> Chapter:
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    allow_references(chapter, bibliography)
    return chapter


@pytest.fixture
def url(chapter: Chapter) -> str:
    return create_chapter_url(chapter, "/lines")


def _make_line_details(
    chapter: Chapter, bibliography: Bibliography
) -> LineDetailsDisplay:
    injector = ManuscriptReferenceInjector(bibliography)
    manuscripts = tuple(map(injector.inject_manuscript, chapter.manuscripts))

    return LineDetailsDisplay.from_line_manuscripts(chapter.lines[0], manuscripts)


def test_get(
    client: testing.TestClient,
    stored_chapter: Chapter,
    bibliography: Bibliography,
    url: str,
) -> None:
    line_details = _make_line_details(stored_chapter, bibliography)

    get_result = simulate_get(client, f"{url}/0")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == LineDetailsDisplaySchema().dump(line_details)


def test_get_too_large_to_cache(
    assert_served_without_caching: Callable[[str], None],
    stored_chapter: Chapter,
    url: str,
) -> None:
    assert_served_without_caching(f"{url}/0")


def test_chapter_not_found(client, text_repository, text, chapter, url):
    text_repository.create(text)

    result = client.simulate_get(f"{url}/0")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_line_not_found(
    client: testing.TestClient, stored_chapter: Chapter, url: str
) -> None:
    result = client.simulate_get(f"{url}/{len(stored_chapter.lines)}")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_line(
    client: testing.TestClient, stored_chapter: Chapter, url: str
) -> None:
    result = client.simulate_get(f"{url}/invalid")

    assert result.status == falcon.HTTP_NOT_FOUND
