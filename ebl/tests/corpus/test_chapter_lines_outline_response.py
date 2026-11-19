import json
from typing import Any, Dict, List, cast

import attr
import falcon
import pytest
from falcon import testing

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.outline_support import create_outline_chapter, dump_outline
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign import Sign

EDITED_INDEX = 2
EDITED_NUMBER = LineNumber(9, True)


def update_chapter(chapter: Chapter, index: int) -> Chapter:
    edited_line = attr.evolve(
        chapter.lines[index],
        number=EDITED_NUMBER,
        is_beginning_of_section=not chapter.lines[index].is_beginning_of_section,
    )
    return attr.evolve(
        chapter,
        lines=tuple(
            (edited_line if line_index == index else line).set_variant_alignment_flags()
            for line_index, line in enumerate(chapter.lines)
        ),
        parser_version=ATF_PARSER_VERSION,
    )


def create_body(updated_chapter: Chapter, index: int) -> str:
    line = create_chapter_dto(updated_chapter)["lines"][index]
    return json.dumps(
        {"new": [], "deleted": [], "edited": [{"index": index, "line": line}]}
    )


def post_lines(
    client: testing.TestClient, chapter: Chapter, body: str, query_string: str
) -> testing.Result:
    result = client.simulate_post(
        create_chapter_url(chapter, "/lines"), body=body, query_string=query_string
    )
    assert isinstance(result, testing.Result)
    return result


@pytest.fixture
def allowed_signs(sign_repository: SignRepository, signs: List[Sign]) -> None:
    allow_signs(signs, sign_repository)


@pytest.fixture
def chapter(
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    allowed_signs: None,
) -> Chapter:
    chapter = create_outline_chapter()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    return chapter


def test_updating_lines_with_outline_view(
    client: testing.TestClient, chapter: Chapter
) -> None:
    updated_chapter = update_chapter(chapter, EDITED_INDEX)

    post_result = post_lines(
        client, chapter, create_body(updated_chapter, EDITED_INDEX), "view=outline"
    )
    outline = cast(Dict[str, Any], post_result.json)

    assert post_result.status == falcon.HTTP_OK
    assert outline == dump_outline(updated_chapter)
    assert outline != dump_outline(chapter)
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
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    allowed_signs: None,
    query_string: str,
) -> None:
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
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
