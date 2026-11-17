from typing import Callable, cast
from unittest.mock import patch

import attr
import falcon
import pytest
from falcon import testing

from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.text import Text
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.support import create_chapter_url, simulate_get
from ebl.tests.factories.corpus import ChapterFactory, TextFactory, LineFactory
from ebl.transliteration.application.parallel_line_injector import (
    ParallelLineInjector,
)


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
    text_repository: MongoTextRepository, text: Text, chapter: Chapter
) -> Chapter:
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    return chapter


@pytest.fixture
def url(chapter: Chapter) -> str:
    return create_chapter_url(chapter, "/display")


def test_get(
    client: testing.TestClient,
    parallel_line_injector: ParallelLineInjector,
    text: Text,
    stored_chapter: Chapter,
    url: str,
) -> None:
    chapter_display = ChapterDisplay.of_chapter(text, stored_chapter)
    injected_chapter_display = attr.evolve(
        chapter_display,
        lines=tuple(
            attr.evolve(
                line,
                variants=tuple(
                    attr.evolve(
                        variant,
                        parallel_lines=parallel_line_injector.inject(
                            variant.parallel_lines
                        ),
                    )
                    for variant in line.variants
                ),
            )
            for line in chapter_display.lines
        ),
    )

    get_result = simulate_get(client, url)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == ChapterDisplaySchema().dump(injected_chapter_display)


def test_get_partial(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    parallel_line_injector: ParallelLineInjector,
) -> None:
    chapter = ChapterFactory.build(lines=LineFactory.build_batch(2, manuscript_id=1))
    text = TextFactory.build(
        genre=chapter.text_id.genre,
        category=chapter.text_id.category,
        index=chapter.text_id.index,
    )
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    chapter_display = ChapterDisplay.of_chapter(text, chapter)
    injected_chapter_display = attr.evolve(
        chapter_display,
        lines=tuple(
            attr.evolve(
                line,
                variants=tuple(
                    attr.evolve(
                        variant,
                        parallel_lines=parallel_line_injector.inject(
                            variant.parallel_lines
                        ),
                    )
                    for variant in line.variants
                ),
            )
            for line in chapter_display.lines
        ),
    )
    url = create_chapter_url(chapter, "/display?lines=0&variants=0")
    serialized_partial_chapter = cast(
        dict, ChapterDisplaySchema().dump(injected_chapter_display)
    )
    selected_line = serialized_partial_chapter["lines"][0]
    serialized_partial_chapter["lines"] = [
        {**selected_line, "variants": selected_line["variants"][:1]}
    ]

    get_result = simulate_get(client, url)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == serialized_partial_chapter


def test_get_cached_and_refresh_after_repository_update(
    cached_client: testing.TestClient,
    text_repository: MongoTextRepository,
    text: Text,
    chapter: Chapter,
    url: str,
) -> None:
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    with patch.object(
        Corpus,
        "find_chapter_for_display",
        autospec=True,
        side_effect=Corpus.find_chapter_for_display,
    ) as find_display:
        first_result = simulate_get(cached_client, url)
        assert first_result.status == falcon.HTTP_OK
        cached_result = simulate_get(cached_client, url)
        assert cached_result.status == falcon.HTTP_OK
        assert first_result.json == cached_result.json
        assert find_display.call_count == 1
        updated_chapter = attr.evolve(chapter, lines=[])
        text_repository.update(updated_chapter.id_, updated_chapter)
        second_result = simulate_get(cached_client, url)
        assert second_result.status == falcon.HTTP_OK
        assert second_result.json == ChapterDisplaySchema().dump(
            ChapterDisplay.of_chapter(text, updated_chapter)
        )
        assert first_result.json != second_result.json
        assert find_display.call_count == 2
        refreshed_cache_result = simulate_get(cached_client, url)
        assert refreshed_cache_result.status == falcon.HTTP_OK
        assert refreshed_cache_result.json == second_result.json
        assert find_display.call_count == 2


def test_get_too_large_to_cache(
    assert_served_without_caching: Callable[[str], None],
    stored_chapter: Chapter,
    url: str,
) -> None:
    assert_served_without_caching(url)


def test_text_not_found(client, text_repository, text, url):
    text_repository.create(text)

    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND


def test_chapter_not_found(client, text_repository, chapter, url):
    text_repository.create_chapter(chapter)

    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND
