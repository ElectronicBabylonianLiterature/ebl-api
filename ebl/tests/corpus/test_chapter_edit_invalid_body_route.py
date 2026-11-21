import json
from typing import Callable

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_edit_support import (
    IMPORT_SUFFIX,
    INVALID_ATF,
    MANUSCRIPTS_SUFFIX,
    ChapterEditKind,
    ChapterEditRequest,
    post_edit,
)
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    find_stored_chapter,
)
from ebl.tests.corpus.outline_support import create_outline_chapter

GUARDED_QUERY = "view=outline&revision=legacy"
EMPTY_MANUSCRIPTS = {"manuscripts": [], "uncertainFragments": []}
REJECTED_REQUESTS = (
    (ChapterEditRequest(IMPORT_SUFFIX, "{}"), falcon.HTTP_BAD_REQUEST),
    (
        ChapterEditRequest(IMPORT_SUFFIX, json.dumps({"atf": 1})),
        falcon.HTTP_BAD_REQUEST,
    ),
    (
        ChapterEditRequest(IMPORT_SUFFIX, json.dumps({"atf": ""})),
        falcon.HTTP_UNPROCESSABLE_ENTITY,
    ),
    (
        ChapterEditRequest(IMPORT_SUFFIX, json.dumps({"atf": INVALID_ATF})),
        falcon.HTTP_UNPROCESSABLE_ENTITY,
    ),
    (ChapterEditRequest(MANUSCRIPTS_SUFFIX, "{}"), falcon.HTTP_BAD_REQUEST),
    (
        ChapterEditRequest(
            MANUSCRIPTS_SUFFIX, json.dumps({**EMPTY_MANUSCRIPTS, "manuscripts": [{}]})
        ),
        falcon.HTTP_BAD_REQUEST,
    ),
    (
        ChapterEditRequest(
            MANUSCRIPTS_SUFFIX,
            json.dumps({**EMPTY_MANUSCRIPTS, "uncertainFragments": ["invalid"]}),
        ),
        falcon.HTTP_BAD_REQUEST,
    ),
    (
        ChapterEditRequest(MANUSCRIPTS_SUFFIX, json.dumps(EMPTY_MANUSCRIPTS)),
        falcon.HTTP_UNPROCESSABLE_ENTITY,
    ),
)


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_outline_chapter())


def assert_rejected_as_without_parameters(
    client: testing.TestClient,
    chapter: Chapter,
    request: ChapterEditRequest,
    expected_status: str,
) -> None:
    result = post_edit(client, chapter, request, GUARDED_QUERY)
    result_without_parameters = post_edit(client, chapter, request, "")

    assert result.status == expected_status
    assert result_without_parameters.status == expected_status
    assert result.json == result_without_parameters.json


@pytest.mark.parametrize("request_,expected_status", REJECTED_REQUESTS)
def test_saving_a_rejected_body(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    request_: ChapterEditRequest,
    expected_status: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    assert_rejected_as_without_parameters(client, chapter, request_, expected_status)

    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_saving_an_invalid_edit(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    edit_kind: ChapterEditKind,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    assert_rejected_as_without_parameters(
        client,
        chapter,
        edit_kind.create_invalid_edit(chapter),
        falcon.HTTP_UNPROCESSABLE_ENTITY,
    )

    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_stale_revision_is_reported_before_an_invalid_edit(
    client: testing.TestClient, chapter: Chapter, edit_kind: ChapterEditKind
) -> None:
    result = post_edit(
        client, chapter, edit_kind.create_invalid_edit(chapter), "revision=stale"
    )

    assert result.status == falcon.HTTP_CONFLICT
