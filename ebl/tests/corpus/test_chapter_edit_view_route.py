from typing import Callable

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import (
    ChapterEdit,
    ChapterEditKind,
    post_edit,
)
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)
from ebl.tests.corpus.outline_support import create_outline_chapter, dump_outline
from ebl.tests.corpus.support import (
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)

CHAPTER_VIEW_QUERIES = (
    "",
    "view=chapter",
    "revision=legacy",
    "view=chapter&revision=legacy",
)
UNKNOWN_VIEW_QUERIES = (
    "view=lines",
    "view=Outline",
    "view=",
    "view=outline&view=chapter",
)


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


@pytest.mark.parametrize("query_string", CHAPTER_VIEW_QUERIES)
def test_chapter_view_is_the_chapter_the_corpus_returns(
    client: testing.TestClient,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    save_sibling_with_corpus: Callable[[Chapter, ChapterEdit], Chapter],
    query_string: str,
) -> None:
    edit = edit_kind.create_edit(chapter, 0)
    expected = save_sibling_with_corpus(chapter, edit)

    result = post_edit(client, chapter, edit, query_string)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(expected)
    assert "revision" not in read_json(result)
    assert simulate_get(client, create_chapter_url(chapter)).json == result.json


def test_outline_view_is_the_outline_at_the_stored_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    edit = edit_kind.create_edit(chapter, 0)

    result = post_edit(client, chapter, edit, "view=outline")
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == edit.update_outline(dump_outline(chapter, revision))
    assert result.json != dump_outline(chapter, revision)
    assert revision != LEGACY_REVISION


def test_outline_view_equals_the_outline_route_after_the_save(
    client: testing.TestClient, chapter: Chapter, edit_kind: ChapterEditKind
) -> None:
    result = post_edit(
        client, chapter, edit_kind.create_edit(chapter, 0), "view=outline"
    )
    outline_result = simulate_get(client, create_chapter_url(chapter, "/outline"))

    assert outline_result.status == falcon.HTTP_OK
    assert outline_result.json == result.json


@pytest.mark.parametrize("query_string", UNKNOWN_VIEW_QUERIES)
def test_saving_with_an_unknown_view(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    query_string: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_edit(client, chapter, edit_kind.create_edit(chapter, 0), query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize(
    "query_string", ["view=outline", "view=outline&revision=legacy"]
)
def test_saving_an_unknown_chapter(
    client: testing.TestClient,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    query_string: str,
) -> None:
    missing_chapter = attr.evolve(chapter, name=f"{chapter.name} missing")

    result = post_edit(
        client, missing_chapter, edit_kind.create_edit(chapter, 0), query_string
    )

    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "query_string", ["", "view=outline", "view=outline&revision=legacy"]
)
def test_saving_requires_write_scope(
    guest_client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
    query_string: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_edit(
        guest_client, chapter, edit_kind.create_edit(chapter, 0), query_string
    )

    assert result.status == falcon.HTTP_FORBIDDEN
    assert find_stored_chapter(database, chapter) == stored_chapter
