import json
from typing import cast

import attr
import falcon
import pytest

from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.domain.stage import Stage
from ebl.corpus.web.chapter_schemas import ApiLineSchema
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
)
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine


EMPTY_EDIT_DTO = {"new": [], "deleted": [], "edited": []}


def test_updating(
    client, bibliography, sign_repository, signs, text_repository
) -> None:
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    updated_chapter = attr.evolve(
        chapter,
        lines=(attr.evolve(chapter.lines[0], number=LineNumber(1, True)),),
        parser_version=ATF_PARSER_VERSION,
    )

    body = {
        "new": [],
        "deleted": [],
        "edited": [
            {"index": index, "line": line}
            for index, line in enumerate(create_chapter_dto(updated_chapter)["lines"])
        ],
    }
    post_result = client.simulate_post(
        create_chapter_url(chapter, "/lines"), body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_chapter_dto(updated_chapter)

    get_result = client.simulate_get(create_chapter_url(chapter))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_chapter_dto(updated_chapter)


def test_updating_strophic_information(
    client, bibliography, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    updated_chapter = attr.evolve(
        chapter,
        lines=(
            attr.evolve(
                chapter.lines[0],
                is_second_line_of_parallelism=not chapter.lines[
                    0
                ].is_second_line_of_parallelism,
                is_beginning_of_section=not chapter.lines[0].is_beginning_of_section,
            ),
        ),
        parser_version=ATF_PARSER_VERSION,
    )

    body = {
        "new": [],
        "deleted": [],
        "edited": [
            {"index": index, "line": line}
            for index, line in enumerate(create_chapter_dto(updated_chapter)["lines"])
        ],
    }
    post_result = client.simulate_post(
        create_chapter_url(chapter, "/lines"), body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_chapter_dto(updated_chapter)

    get_result = client.simulate_get(create_chapter_url(chapter))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_chapter_dto(updated_chapter)


def test_updating_chapter_not_found(client, bibliography):
    post_result = client.simulate_post(
        f"/texts/1/1/chapters/{Stage.STANDARD_BABYLONIAN.value}/any/lines",
        body=json.dumps(EMPTY_EDIT_DTO),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_category(client):
    post_result = client.simulate_post(
        f"/texts/invalid/1/chapters/{Stage.STANDARD_BABYLONIAN.value}/any/lines",
        body=json.dumps(EMPTY_EDIT_DTO),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_id(client):
    post_result = client.simulate_post(
        "/texts/1/invalid/chapters/any/any/lines", body=json.dumps(EMPTY_EDIT_DTO)
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


TOO_MANY_NOTES = {
    **ApiLineSchema().dump(ChapterFactory.build().lines[0]),
    "reconstruction": "kur\n#note: extra note\n#note: extra note",
}


@pytest.mark.parametrize(
    "dto,expected_status",
    [
        [[], falcon.HTTP_BAD_REQUEST],
        [{}, falcon.HTTP_BAD_REQUEST],
        [
            {
                "new": [],
                "deleted": [],
                "edited": [{"index": 0, "line": TOO_MANY_NOTES}],
            },
            falcon.HTTP_BAD_REQUEST,
        ],
    ],
)
def test_update_invalid_entity(
    client, bibliography, dto, expected_status, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/lines"), body=json.dumps(dto)
    )

    assert post_result.status == expected_status


def test_importing(client, bibliography, sign_repository, signs, text_repository):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    next_line_mumber = (
        cast(
            TextLine, chapter.lines[0].variants[0].manuscripts[0].line
        ).line_number.number
        + 1
    )
    atf = (
        f"{chapter.lines[0].number.number+1}. bu\n"
        f"{str(chapter.manuscripts[0].siglum)} {next_line_mumber}. ..."
    )

    updated_chapter = attr.evolve(
        chapter,
        lines=(*chapter.lines, *parse_chapter(atf, chapter.manuscripts)),
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\n\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )

    body = {"atf": atf}
    post_result = client.simulate_post(
        create_chapter_url(chapter, "/import"), body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_chapter_dto(updated_chapter)

    get_result = client.simulate_get(create_chapter_url(chapter))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_chapter_dto(updated_chapter)


@pytest.mark.parametrize(
    "body,expected_status",
    [
        [{}, falcon.HTTP_BAD_REQUEST],
        [{"atf": ""}, falcon.HTTP_UNPROCESSABLE_ENTITY],
        [{"atf": "invalid atf"}, falcon.HTTP_UNPROCESSABLE_ENTITY],
    ],
)
def test_import_invalid_entity(
    client, bibliography, body, expected_status, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/import"), body=json.dumps(body)
    )

    assert post_result.status == expected_status
