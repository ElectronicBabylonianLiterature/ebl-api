import attr
import falcon
import pytest

from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.text import Text
from ebl.tests.corpus.support import create_chapter_url
from ebl.tests.factories.corpus import ChapterFactory, TextFactory, LineFactory


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


def test_get(client, text_repository, parallel_line_injector, text, chapter, url):
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

    get_result = client.simulate_get(url)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == ChapterDisplaySchema().dump(injected_chapter_display)


def test_get_partial(
    client,
    text_repository,
    parallel_line_injector,
):
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
    serialized_partial_chapter = ChapterDisplaySchema().dump(injected_chapter_display)
    selected_line = serialized_partial_chapter["lines"][0]
    serialized_partial_chapter["lines"] = [
        {**selected_line, "variants": selected_line["variants"][:1]}
    ]

    get_result = client.simulate_get(url)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == serialized_partial_chapter


def test_get_cached(cached_client, text_repository, text, chapter, url):
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    first_result = cached_client.simulate_get(url)
    assert first_result.status == falcon.HTTP_OK
    updated_chapter = attr.evolve(chapter, lines=[])
    text_repository.update(updated_chapter.id_, updated_chapter)
    second_result = cached_client.simulate_get(url)
    assert second_result.status == falcon.HTTP_OK
    assert first_result.json == second_result.json


def test_text_not_found(client, text_repository, text, url):
    text_repository.create(text)

    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND


def test_chapter_not_found(client, text_repository, chapter, url):
    text_repository.create_chapter(chapter)

    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND
