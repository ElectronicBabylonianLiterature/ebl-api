import json
from typing import Any, Callable, Dict, cast

import attr
import falcon
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.lines_edit_support import (
    EDITED_INDEX,
    create_body,
    post_lines,
    update_chapter,
)
from ebl.tests.corpus.outline_support import create_outline_chapter, dump_outline
from ebl.tests.corpus.support import (
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)
from ebl.tests.factories.corpus import ChapterFactory


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


def test_updating_lines_with_outline_view(
    client: testing.TestClient, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    updated_chapter = update_chapter(chapter, EDITED_INDEX)

    post_result = post_lines(
        client, chapter, create_body(updated_chapter, EDITED_INDEX), "view=outline"
    )
    outline = cast(Dict[str, Any], post_result.json)
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert post_result.status == falcon.HTTP_OK
    assert outline == dump_outline(updated_chapter, revision)
    assert outline != dump_outline(chapter, revision)
    assert outline != dump_outline(updated_chapter)
    assert outline["lines"][EDITED_INDEX]["number"] == "9'"
    assert [line["index"] for line in outline["lines"]] == [0, 1, 2]


def test_outline_view_equals_the_outline_route_after_the_update(
    client: testing.TestClient, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    updated_chapter = update_chapter(chapter, EDITED_INDEX)

    post_result = post_lines(
        client, chapter, create_body(updated_chapter, EDITED_INDEX), "view=outline"
    )
    get_result = simulate_get(client, create_chapter_url(chapter, "/outline"))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == post_result.json
    assert text_repository.find_chapter(chapter.id_).lines == updated_chapter.lines


@pytest.mark.parametrize("query_string", ["", "view=chapter", "offset=1&limit=1"])
def test_updating_lines_without_outline_view(
    client: testing.TestClient,
    store_editable_chapter: Callable[[Chapter], Chapter],
    query_string: str,
) -> None:
    chapter = store_editable_chapter(ChapterFactory.build())
    updated_chapter = update_chapter(chapter, 0)

    post_result = post_lines(
        client, chapter, create_body(updated_chapter, 0), query_string
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == create_chapter_dto(updated_chapter)
    assert simulate_get(client, create_chapter_url(chapter)).json == create_chapter_dto(
        updated_chapter
    )


@pytest.mark.parametrize(
    "query_string",
    ["view=lines", "view=Outline", "view=", "view=outline&view=chapter"],
)
def test_updating_lines_with_unknown_view(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    query_string: str,
) -> None:
    body = create_body(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)

    post_result = post_lines(client, chapter, body, query_string)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert text_repository.find_chapter(chapter.id_).lines == chapter.lines


@pytest.mark.parametrize("body", ["{}", "[]", json.dumps({"new": [], "deleted": []})])
def test_updating_lines_with_outline_view_and_invalid_body(
    client: testing.TestClient, chapter: Chapter, body: str
) -> None:
    post_result = post_lines(client, chapter, body, "view=outline")

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_updating_lines_with_outline_view_of_unknown_chapter(
    client: testing.TestClient, chapter: Chapter
) -> None:
    missing_chapter = attr.evolve(chapter, name=f"{chapter.name} missing")
    body = create_body(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)

    post_result = post_lines(client, missing_chapter, body, "view=outline")

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_lines_with_outline_view_requires_write_scope(
    guest_client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
) -> None:
    body = create_body(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)

    post_result = post_lines(guest_client, chapter, body, "view=outline")

    assert post_result.status == falcon.HTTP_FORBIDDEN
    assert text_repository.find_chapter(chapter.id_).lines == chapter.lines
