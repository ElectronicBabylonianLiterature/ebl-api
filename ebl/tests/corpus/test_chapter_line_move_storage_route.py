from functools import reduce
from typing import Sequence

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.tests.corpus.line_move_support import (
    MOVE_QUERY,
    MOVES,
    STORED_PARSER_VERSION,
    assert_lines_are_annotated,
    invert,
    move_chapter_line,
    post_move,
    reorder,
)
from ebl.tests.corpus.lines_edit_support import find_stored_chapter, read_json
from ebl.tests.corpus.outline_support import dump_outline, remove_key
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION

MOVED_FIELDS: Sequence[str] = ("lines", "signs", REVISION_FIELD)


def test_lines_of_the_chapter_are_annotated(move_chapter: Chapter) -> None:
    assert_lines_are_annotated(move_chapter.lines)
    assert STORED_PARSER_VERSION != ATF_PARSER_VERSION


@pytest.mark.parametrize("move", MOVES)
def test_moved_lines_are_stored_with_their_signs(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    registered_sign_repository: SignRepository,
    move_chapter: Chapter,
    move: LineMove,
) -> None:
    reordered_lines = reorder(move_chapter.lines, move)

    result = post_move(client, move_chapter, move, MOVE_QUERY)
    found = text_repository.find_chapter(move_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert found.lines == reordered_lines
    assert_lines_are_annotated(found.lines)
    assert found.signs == (
        SignsUpdater(registered_sign_repository)
        .update(attr.evolve(move_chapter, lines=reordered_lines, signs=()))
        .signs
    )
    assert found.signs != move_chapter.signs


@pytest.mark.parametrize("move", MOVES)
def test_move_changes_nothing_but_the_order_and_the_signs(
    client: testing.TestClient, corpus: Corpus, move_chapter: Chapter, move: LineMove
) -> None:
    result = post_move(client, move_chapter, move, MOVE_QUERY)
    found = corpus.find_chapter(move_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert found == move_chapter_line(move_chapter, move)
    assert found.parser_version == STORED_PARSER_VERSION
    assert found.manuscripts == move_chapter.manuscripts
    assert found.uncertain_fragments == move_chapter.uncertain_fragments


@pytest.mark.parametrize("move", MOVES)
def test_move_only_reorders_the_stored_lines(
    client: testing.TestClient,
    database: Database,
    move_chapter: Chapter,
    move: LineMove,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)

    result = post_move(client, move_chapter, move, MOVE_QUERY)
    moved_chapter = find_stored_chapter(database, move_chapter)

    assert result.status == falcon.HTTP_OK
    assert moved_chapter["lines"] == list(reorder(stored_chapter["lines"], move))
    assert moved_chapter["lines"] != stored_chapter["lines"]
    assert reduce(remove_key, MOVED_FIELDS, moved_chapter) == reduce(
        remove_key, MOVED_FIELDS, stored_chapter
    )


@pytest.mark.parametrize("move", MOVES)
def test_moving_there_and_back_restores_the_stored_chapter(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    move_chapter: Chapter,
    move: LineMove,
) -> None:
    stored_chapter = find_stored_chapter(database, move_chapter)
    first_result = post_move(client, move_chapter, move, MOVE_QUERY)
    first_revision = read_json(first_result)["revision"]

    second_result = post_move(
        client, move_chapter, invert(move), f"view=outline&revision={first_revision}"
    )
    restored_chapter = find_stored_chapter(database, move_chapter)
    found = text_repository.find_chapter(move_chapter.id_)

    assert second_result.status == falcon.HTTP_OK
    assert second_result.json == dump_outline(
        move_chapter, restored_chapter[REVISION_FIELD]
    )
    assert restored_chapter[REVISION_FIELD] != first_revision
    assert remove_key(restored_chapter, REVISION_FIELD) == stored_chapter
    assert found.lines == move_chapter.lines
    assert found.signs == move_chapter.signs
