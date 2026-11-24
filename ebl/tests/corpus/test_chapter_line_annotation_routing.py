from typing import Callable, Sequence

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_annotation_kind import ANNOTATION_QUERY, AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import (
    ALIGNMENT,
    ANNOTATION_KINDS,
    LEMMATIZATION,
)
from ebl.tests.corpus.line_annotation_support import ANNOTATION_LINE_COUNT
from ebl.tests.corpus.line_move_support import MOVE, move_chapter_line, post_move
from ebl.tests.corpus.lines_edit_support import (
    EDITED_INDEX,
    LINES_SUFFIX,
    create_body,
    find_stored_chapter,
    get_lines,
    post_lines,
    read_json,
    update_chapter,
)
from ebl.tests.corpus.outline_support import dump_outline
from ebl.tests.corpus.support import (
    create_chapter_url,
    dump_line_details,
    get_line,
    simulate_get,
)

CACHED_SUFFIXES: Sequence[str] = ("/display", "/lines/0")
UNROUTED_SUFFIXES: Sequence[str] = (
    "/lines/0/alignment/0",
    "/lines/0/lemmatization/0",
    "/lines/0/move",
    "/lines/alignment/0",
)


@pytest.fixture
def chapter(
    store_text: Callable[[Chapter], Chapter], annotation_chapter: Chapter
) -> Chapter:
    return store_text(annotation_chapter)


def find_revision(result: testing.Result) -> str:
    assert result.status == falcon.HTTP_OK
    return read_json(result)["revision"]


@pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))
def test_line_route_returns_the_line_at_the_position(
    client: testing.TestClient, chapter: Chapter, index: int
) -> None:
    result = get_line(client, chapter, index)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_line_details(chapter, index)


def test_lines_route_returns_a_page(
    client: testing.TestClient, chapter: Chapter
) -> None:
    result = get_lines(client, chapter, "offset=1&limit=2")

    assert result.status == falcon.HTTP_OK
    assert read_json(result)["total"] == ANNOTATION_LINE_COUNT
    assert [line["number"] for line in read_json(result)["lines"]] == ["2", "3"]


def test_every_line_save_reaches_its_own_resource(
    client: testing.TestClient, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    moved_chapter = move_chapter_line(chapter, MOVE)
    edited_chapter = update_chapter(moved_chapter, EDITED_INDEX)
    aligned_chapter = ALIGNMENT.update_chapter(edited_chapter, 0)
    lemmatized_chapter = LEMMATIZATION.update_chapter(aligned_chapter, 1)

    move_revision = find_revision(post_move(client, chapter, MOVE, ANNOTATION_QUERY))
    edit_revision = find_revision(
        post_lines(
            client,
            chapter,
            create_body(edited_chapter, EDITED_INDEX),
            f"view=outline&revision={move_revision}",
        )
    )
    alignment_revision = find_revision(
        ALIGNMENT.post_new(
            client, edited_chapter, 0, f"view=outline&revision={edit_revision}"
        )
    )
    result = LEMMATIZATION.post_new(
        client, aligned_chapter, 1, f"view=outline&revision={alignment_revision}"
    )

    assert result.json == dump_outline(lemmatized_chapter, find_revision(result))
    assert text_repository.find_chapter(chapter.id_).lines == lemmatized_chapter.lines
    assert len({edit_revision, move_revision, alignment_revision}) == 3


def test_getting_a_line_save_route_is_not_allowed(
    client: testing.TestClient, chapter: Chapter, annotation_kind: AnnotationKind
) -> None:
    result = simulate_get(
        client, create_chapter_url(chapter, f"/lines/0/{annotation_kind.name}")
    )

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("suffix", [LINES_SUFFIX, "/lines/0", "/lines/move"])
def test_posting_an_annotation_to_another_line_route_does_not_save_it(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    annotation_kind: AnnotationKind,
    suffix: str,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    body = annotation_kind.create_new_request(chapter, 0).body

    result = post_edit(
        client, chapter, ChapterEditRequest(suffix, body), ANNOTATION_QUERY
    )

    assert result.status in (falcon.HTTP_BAD_REQUEST, falcon.HTTP_METHOD_NOT_ALLOWED)
    assert find_stored_chapter(database, chapter) == stored_chapter


@pytest.mark.parametrize("suffix", UNROUTED_SUFFIXES)
def test_longer_paths_are_not_routed(
    client: testing.TestClient, database: Database, chapter: Chapter, suffix: str
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    body = ALIGNMENT.create_new_request(chapter, 0).body

    result = post_edit(
        client, chapter, ChapterEditRequest(suffix, body), ANNOTATION_QUERY
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert find_stored_chapter(database, chapter) == stored_chapter


@pytest.mark.parametrize("kind", ANNOTATION_KINDS, ids=lambda kind: kind.name)
def test_save_invalidates_the_cached_displays(
    client: testing.TestClient,
    database: Database,
    chapter: Chapter,
    kind: AnnotationKind,
) -> None:
    endpoints = [create_chapter_url(chapter, suffix) for suffix in CACHED_SUFFIXES]
    cached_display, cached_line = (
        simulate_get(client, endpoint) for endpoint in endpoints
    )
    cached_count = database[COLLECTION].count_documents({})

    result = kind.post_new(client, chapter, 0)
    count_after_save = database[COLLECTION].count_documents({})
    display, line = (simulate_get(client, endpoint) for endpoint in endpoints)

    assert result.status == falcon.HTTP_OK
    assert cached_count == len(endpoints)
    assert count_after_save == 0
    assert display.json != cached_display.json
    assert line.json == dump_line_details(kind.update_chapter(chapter, 0), 0)
    assert line.json != cached_line.json
    assert database[COLLECTION].count_documents({}) == len(endpoints)
