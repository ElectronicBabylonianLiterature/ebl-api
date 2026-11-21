import json
from itertools import cycle
from typing import Callable, Sequence, Tuple

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_move import LineMove
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_move_support import (
    EXTENT_BREAKING_MOVES,
    MOVE,
    MOVE_QUERY,
    MOVE_SUFFIX,
    create_extent_chapter,
    create_move_chapter,
    post_move,
)
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)

REVISION_REQUIRED = "revision is required"
INVALID_REVISION = "revision must be a non-empty string, got {} instead"
INVALID_POSITION = "Invalid line move: {} is not a line position (number of lines: 4)."
SAME_POSITION = "Invalid line move: the line is already at that position."
MALFORMED_BODIES: Sequence[Tuple[object, Sequence[str]]] = (
    ({}, ["from", "to"]),
    ({"from": 0}, ["to"]),
    ({"to": 2}, ["from"]),
    ({"from": "0", "to": 2}, ["from"]),
    ({"from": 0, "to": "2"}, ["to"]),
    ({"from": True, "to": 2}, ["from"]),
    ({"from": 0, "to": False}, ["to"]),
    ({"from": 0.0, "to": 2}, ["from"]),
    ({"from": 0, "to": 2.5}, ["to"]),
    ({"from": -1, "to": 2}, ["from"]),
    ({"from": 0, "to": -2}, ["to"]),
    ({"from": None, "to": 2}, ["from"]),
    ({"from": [0], "to": 2}, ["from"]),
    ({"from": 0, "to": {"index": 2}}, ["to"]),
    ({"from": 0, "to": 2, "line": 1}, ["line"]),
    ({"source": 0, "target": 2}, ["from", "source", "target", "to"]),
    ([], ["_schema"]),
    ([0, 2], ["_schema"]),
    (None, ["_schema"]),
    ("move", ["_schema"]),
    (2, ["_schema"]),
)


@attr.s(frozen=True, auto_attribs=True)
class RefusedMove:
    move: LineMove
    query_string: str
    description: str
    create_chapter: Callable[[], Chapter] = create_move_chapter


REFUSED_MOVES: Sequence[RefusedMove] = (
    RefusedMove(MOVE, "", REVISION_REQUIRED),
    RefusedMove(MOVE, "view=outline", REVISION_REQUIRED),
    RefusedMove(MOVE, "view=chapter", REVISION_REQUIRED),
    RefusedMove(MOVE, "view=outline&revision=", INVALID_REVISION.format("''")),
    RefusedMove(MOVE, "revision=a&revision=b", INVALID_REVISION.format("['a', 'b']")),
    RefusedMove(MOVE, "view=lines&revision=legacy", "unexpected view 'lines'"),
    RefusedMove(LineMove(4, 0), MOVE_QUERY, INVALID_POSITION.format("from 4")),
    RefusedMove(LineMove(4, 4), MOVE_QUERY, INVALID_POSITION.format("from 4")),
    RefusedMove(
        LineMove(10**20, 0), MOVE_QUERY, INVALID_POSITION.format(f"from {10**20}")
    ),
    RefusedMove(LineMove(0, 4), MOVE_QUERY, INVALID_POSITION.format("to 4")),
    RefusedMove(LineMove(0, 4), "revision=legacy", INVALID_POSITION.format("to 4")),
    RefusedMove(LineMove(0, 0), MOVE_QUERY, SAME_POSITION),
    RefusedMove(LineMove(3, 3), "revision=legacy", SAME_POSITION),
    *(
        RefusedMove(move, query_string, message, create_extent_chapter)
        for (move, message), query_string in zip(
            EXTENT_BREAKING_MOVES, cycle((MOVE_QUERY, "revision=legacy"))
        )
    ),
)


@pytest.mark.parametrize("refused", REFUSED_MOVES)
def test_refused_move(
    client: testing.TestClient,
    database: Database,
    store_editable_chapter: Callable[[Chapter], Chapter],
    refused: RefusedMove,
) -> None:
    chapter = store_editable_chapter(refused.create_chapter())
    stored_chapter = find_stored_chapter(database, chapter)

    result = post_move(client, chapter, refused.move, refused.query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == refused.description
    assert find_stored_chapter(database, chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("body,invalid_fields", MALFORMED_BODIES)
def test_moving_with_a_malformed_body(
    client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    body: object,
    invalid_fields: Sequence[str],
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    request = ChapterEditRequest(MOVE_SUFFIX, json.dumps(body))

    result = post_edit(client, move_chapter, request, MOVE_QUERY)
    result_without_parameters = post_edit(client, move_chapter, request, "")

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert read_json(result)["title"] == "Request data failed validation"
    assert sorted(read_json(result)["description"]) == invalid_fields
    assert result_without_parameters.json == result.json
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


@pytest.mark.parametrize("body", ["", "{", '{"from": 0, "to": 2'])
def test_moving_with_invalid_json(
    client: testing.TestClient, database: Database, move_chapter: Chapter, body: str
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)

    result = post_edit(
        client, move_chapter, ChapterEditRequest(MOVE_SUFFIX, body), MOVE_QUERY
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert find_stored_chapter(database, move_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0
