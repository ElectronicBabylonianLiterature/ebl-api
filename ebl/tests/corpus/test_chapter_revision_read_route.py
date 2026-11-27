from typing import Callable

import falcon
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.lines_edit_support import (
    EDITED_INDEX,
    STALE_REVISION,
    create_body,
    get_lines,
    post_lines,
    read_json,
    update_chapter,
)
from ebl.tests.corpus.outline_support import create_outline_chapter
from ebl.tests.corpus.support import create_chapter_url, simulate_get


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


def get_outline_revision(client: testing.TestClient, chapter: Chapter) -> str:
    result = simulate_get(client, create_chapter_url(chapter, "/outline"))
    assert result.status == falcon.HTTP_OK
    return read_json(result)["revision"]


def get_lines_revision(client: testing.TestClient, chapter: Chapter) -> str:
    result = get_lines(client, chapter, "limit=1")
    assert result.status == falcon.HTTP_OK
    return read_json(result)["revision"]


def save_lines(client: testing.TestClient, chapter: Chapter) -> None:
    body = create_body(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)
    assert post_lines(client, chapter, body, "").status == falcon.HTTP_OK


@pytest.mark.parametrize("get_revision", [get_outline_revision, get_lines_revision])
def test_never_updated_chapter_is_read_at_the_legacy_revision(
    client: testing.TestClient,
    chapter: Chapter,
    get_revision: Callable[[testing.TestClient, Chapter], str],
) -> None:
    assert get_revision(client, chapter) == LEGACY_REVISION


@pytest.mark.parametrize("get_revision", [get_outline_revision, get_lines_revision])
def test_read_revision_changes_with_every_save(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    get_revision: Callable[[testing.TestClient, Chapter], str],
) -> None:
    save_lines(client, chapter)
    first_revision = get_revision(client, chapter)
    save_lines(client, chapter)
    second_revision = get_revision(client, chapter)

    assert second_revision == text_repository.find_chapter_revision(chapter.id_)
    assert LEGACY_REVISION not in (first_revision, second_revision)
    assert first_revision != second_revision


def test_outline_and_lines_page_agree_on_the_revision(
    client: testing.TestClient, chapter: Chapter
) -> None:
    save_lines(client, chapter)

    assert get_outline_revision(client, chapter) == get_lines_revision(client, chapter)


def test_get_lines_at_the_legacy_revision(
    client: testing.TestClient, chapter: Chapter
) -> None:
    result = get_lines(client, chapter, "offset=1&limit=1&revision=legacy")

    assert result.status == falcon.HTTP_OK
    assert result.json == get_lines(client, chapter, "offset=1&limit=1").json
    assert read_json(result)["revision"] == LEGACY_REVISION


def test_get_lines_at_the_current_revision(
    client: testing.TestClient, chapter: Chapter
) -> None:
    save_lines(client, chapter)
    revision = get_outline_revision(client, chapter)

    result = get_lines(client, chapter, f"tokens=true&revision={revision}")

    assert result.status == falcon.HTTP_OK
    assert result.json == get_lines(client, chapter, "tokens=true").json
    assert read_json(result)["revision"] == revision


@pytest.mark.parametrize("stale_revision", [STALE_REVISION, LEGACY_REVISION])
def test_get_lines_at_a_stale_revision(
    client: testing.TestClient, chapter: Chapter, stale_revision: str
) -> None:
    save_lines(client, chapter)
    conflict = chapter_revision_conflict(
        chapter.id_, stale_revision, get_outline_revision(client, chapter)
    )

    result = get_lines(client, chapter, f"limit=1&revision={stale_revision}")

    assert result.status == falcon.HTTP_CONFLICT
    assert read_json(result)["description"] == str(conflict)


def test_get_lines_of_never_updated_chapter_at_a_stale_revision(
    guest_client: testing.TestClient, chapter: Chapter
) -> None:
    result = get_lines(guest_client, chapter, f"revision={STALE_REVISION}")

    assert result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("query_string", ["revision=", "revision=a&revision=b"])
def test_get_lines_with_an_invalid_revision(
    client: testing.TestClient, chapter: Chapter, query_string: str
) -> None:
    result = get_lines(client, chapter, query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_lines_of_an_unknown_chapter_at_a_revision(
    client: testing.TestClient,
) -> None:
    url = "/texts/L/1/1/chapters/Standard Babylonian/unknown/lines"

    result = simulate_get(client, f"{url}?revision=legacy")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_outline_ignores_the_revision_parameter(
    client: testing.TestClient, chapter: Chapter
) -> None:
    url = create_chapter_url(chapter, "/outline")

    result = simulate_get(client, f"{url}?revision={STALE_REVISION}")

    assert result.status == falcon.HTTP_OK
    assert result.json == simulate_get(client, url).json
