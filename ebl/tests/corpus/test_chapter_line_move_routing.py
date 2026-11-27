import json
from typing import Any, Callable, Dict, Iterator, List, Sequence, Tuple

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.line_move import LineMove
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_move_support import (
    LINE_COUNT,
    MOVE,
    MOVE_QUERY,
    MOVE_SUFFIX,
    move_chapter_line,
    post_move,
    reorder,
)
from ebl.tests.corpus.lines_edit_support import find_stored_chapter, read_json
from ebl.tests.corpus.outline_support import remove_key
from ebl.tests.corpus.support import (
    create_chapter_url,
    dump_line_details,
    get_line,
    simulate_get,
)

CACHED_READS: Sequence[Tuple[str, str]] = (
    ("find_chapter_for_display", "/display"),
    ("find_line_with_manuscript_joins", "/lines/0"),
)
CACHED_SUFFIXES: Sequence[str] = tuple(suffix for _, suffix in CACHED_READS)


@pytest.fixture
def chapter(store_text: Callable[[Chapter], Chapter], move_chapter: Chapter) -> Chapter:
    return store_text(move_chapter)


def find_display_lines(result: testing.Result) -> List[Dict[str, Any]]:
    return [remove_key(line, "originalIndex") for line in read_json(result)["lines"]]


@pytest.mark.parametrize("index", range(LINE_COUNT))
def test_line_route_returns_the_line_at_the_position(
    client: testing.TestClient, chapter: Chapter, index: int
) -> None:
    result = get_line(client, chapter, index)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_line_details(chapter, index)


def test_line_route_follows_a_move(
    client: testing.TestClient, chapter: Chapter
) -> None:
    moved_chapter = move_chapter_line(chapter, MOVE)

    result = post_move(client, chapter, MOVE, MOVE_QUERY)

    assert result.status == falcon.HTTP_OK
    assert [get_line(client, chapter, index).json for index in range(LINE_COUNT)] == [
        dump_line_details(moved_chapter, index) for index in range(LINE_COUNT)
    ]


@pytest.mark.parametrize("number", [LINE_COUNT, "first", "1.5"])
def test_line_route_of_an_unknown_line(
    client: testing.TestClient, chapter: Chapter, number: object
) -> None:
    assert get_line(client, chapter, number).status == falcon.HTTP_NOT_FOUND


def test_getting_the_move_route_is_not_allowed(
    client: testing.TestClient, chapter: Chapter
) -> None:
    result = simulate_get(client, create_chapter_url(chapter, MOVE_SUFFIX))

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED


def test_posting_a_move_to_a_line_position_is_not_allowed(
    client: testing.TestClient, database: Database, chapter: Chapter
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    request = ChapterEditRequest("/lines/0", json.dumps({"from": 0, "to": 2}))

    result = post_edit(client, chapter, request, MOVE_QUERY)

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED
    assert find_stored_chapter(database, chapter) == stored_chapter


def test_move_invalidates_the_cached_displays(
    client: testing.TestClient, database: Database, chapter: Chapter
) -> None:
    endpoints = [create_chapter_url(chapter, suffix) for suffix in CACHED_SUFFIXES]
    cached_display, cached_line = (
        simulate_get(client, endpoint) for endpoint in endpoints
    )
    cached_count = database[COLLECTION].count_documents({})

    result = post_move(client, chapter, MOVE, MOVE_QUERY)
    count_after_move = database[COLLECTION].count_documents({})
    display, line = (simulate_get(client, endpoint) for endpoint in endpoints)

    assert result.status == falcon.HTTP_OK
    assert cached_count == len(endpoints)
    assert count_after_move == 0
    assert find_display_lines(display) == list(
        reorder(find_display_lines(cached_display), MOVE)
    )
    assert find_display_lines(display) != find_display_lines(cached_display)
    assert line.json == dump_line_details(move_chapter_line(chapter, MOVE), 0)
    assert line.json != cached_line.json
    assert database[COLLECTION].count_documents({}) == len(endpoints)


@pytest.mark.parametrize("read_method,suffix", CACHED_READS)
def test_read_finishing_after_a_move_does_not_poison_the_cache(
    client: testing.TestClient,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
    read_method: str,
    suffix: str,
) -> None:
    read: Callable[..., object] = getattr(Corpus, read_method)
    moves: Iterator[LineMove] = iter([MOVE])

    def read_before_move(
        corpus: Corpus, chapter_id: ChapterId, *args: object
    ) -> object:
        previous = read(corpus, chapter_id, *args)
        for move in moves:
            assert post_move(client, chapter, move, MOVE_QUERY).status == falcon.HTTP_OK
        return previous

    monkeypatch.setattr(Corpus, read_method, read_before_move)
    endpoint = create_chapter_url(chapter, suffix)
    old_result = simulate_get(client, endpoint)
    fresh_result = simulate_get(client, endpoint)
    reused_result = simulate_get(client, endpoint)

    assert old_result.status == fresh_result.status == falcon.HTTP_OK
    assert old_result.json != fresh_result.json
    assert fresh_result.json == reused_result.json
