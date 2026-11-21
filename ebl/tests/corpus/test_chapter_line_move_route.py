from typing import Sequence

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.line_move_support import (
    EXTENT_KEEPING_MOVES,
    LINE_COUNT,
    MOVE,
    MOVE_QUERY,
    MOVES,
    move_chapter_line,
    post_move,
)
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    read_json,
)
from ebl.tests.corpus.outline_support import dump_outline
from ebl.tests.corpus.support import (
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)

CHAPTER_VIEW_QUERIES = ("revision=legacy", "view=chapter&revision=legacy")


@pytest.mark.parametrize("move", MOVES)
def test_outline_view_is_the_outline_of_the_moved_chapter(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
    move: LineMove,
) -> None:
    result = post_move(client, move_chapter, move, MOVE_QUERY)
    revision = text_repository.find_chapter_revision(move_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_outline(move_chapter_line(move_chapter, move), revision)
    assert result.json != dump_outline(move_chapter, revision)
    assert revision != LEGACY_REVISION


@pytest.mark.parametrize(
    "move,numbers",
    [
        (LineMove(0, 2), ["2", "3", "1", "4"]),
        (LineMove(3, 0), ["4", "1", "2", "3"]),
        (LineMove(1, 2), ["1", "3", "2", "4"]),
        (LineMove(2, 1), ["1", "3", "2", "4"]),
    ],
)
def test_outline_lines_keep_their_numbers_at_the_new_positions(
    client: testing.TestClient,
    move_chapter: Chapter,
    move: LineMove,
    numbers: Sequence[str],
) -> None:
    lines = read_json(post_move(client, move_chapter, move, MOVE_QUERY))["lines"]

    assert [line["index"] for line in lines] == list(range(LINE_COUNT))
    assert [line["number"] for line in lines] == numbers


@pytest.mark.parametrize("query_string", CHAPTER_VIEW_QUERIES)
def test_chapter_view_is_the_moved_chapter(
    client: testing.TestClient, move_chapter: Chapter, query_string: str
) -> None:
    result = post_move(client, move_chapter, MOVE, query_string)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(move_chapter_line(move_chapter, MOVE))
    assert "revision" not in read_json(result)


@pytest.mark.parametrize("move", MOVES)
def test_chapter_route_returns_the_moved_chapter(
    client: testing.TestClient, move_chapter: Chapter, move: LineMove
) -> None:
    post_move(client, move_chapter, move, MOVE_QUERY)

    result = simulate_get(client, create_chapter_url(move_chapter))

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(move_chapter_line(move_chapter, move))
    assert result.json != create_chapter_dto(move_chapter)


def test_outline_view_equals_the_outline_route_after_the_move(
    client: testing.TestClient, move_chapter: Chapter
) -> None:
    result = post_move(client, move_chapter, MOVE, MOVE_QUERY)
    outline_result = simulate_get(client, create_chapter_url(move_chapter, "/outline"))

    assert outline_result.status == falcon.HTTP_OK
    assert outline_result.json == result.json


def test_moving_with_the_revision_of_the_previous_move(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
) -> None:
    other_move = LineMove(3, 1)
    first_result = post_move(client, move_chapter, MOVE, MOVE_QUERY)
    first_revision = read_json(first_result)["revision"]

    second_result = post_move(
        client, move_chapter, other_move, f"view=outline&revision={first_revision}"
    )
    revision = text_repository.find_chapter_revision(move_chapter.id_)

    assert second_result.status == falcon.HTTP_OK
    assert second_result.json == dump_outline(
        move_chapter_line(move_chapter_line(move_chapter, MOVE), other_move), revision
    )
    assert revision != first_revision
    assert count_chapter_changelog_entries(database) == 2


@pytest.mark.parametrize("query_string", [MOVE_QUERY, *CHAPTER_VIEW_QUERIES])
def test_move_writes_one_changelog_entry(
    client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    query_string: str,
) -> None:
    result = post_move(client, move_chapter, MOVE, query_string)

    assert result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("move", EXTENT_KEEPING_MOVES)
def test_move_keeping_a_translation_extent(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    extent_chapter: Chapter,
    move: LineMove,
) -> None:
    result = post_move(client, extent_chapter, move, MOVE_QUERY)
    revision = text_repository.find_chapter_revision(extent_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_outline(
        move_chapter_line(extent_chapter, move), revision
    )
