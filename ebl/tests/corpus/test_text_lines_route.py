import json
from typing import cast

import attr
import falcon
import pytest

from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_schemas import ApiLineSchema
from ebl.tests.factories.corpus import TextFactory
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.users.domain.user import Guest

ANY_USER = Guest()


def create_dto(text):
    return serialize(text)


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_text(client, text):
    post_result = client.simulate_post("/texts", body=json.dumps(create_dto(text)))
    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers["Location"] == f"/texts/{text.category}/{text.index}"
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_dto(text)


def test_updating(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    updated_text = attr.evolve(
        text,
        chapters=(
            attr.evolve(
                text.chapters[0],
                lines=(
                    attr.evolve(text.chapters[0].lines[0], number=LineNumber(1, True)),
                ),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )

    body = {"lines": create_dto(updated_text)["chapters"][0]["lines"]}
    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/lines", body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_dto(updated_text)

    get_result = client.simulate_get(
        f"/texts/{updated_text.category}/{updated_text.index}"
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_dto(updated_text)


def test_updating_strophic_information(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    updated_text = attr.evolve(
        text,
        chapters=(
            attr.evolve(
                text.chapters[0],
                lines=(
                    attr.evolve(
                        text.chapters[0].lines[0],
                        is_second_line_of_parallelism=not text.chapters[0]
                        .lines[0]
                        .is_second_line_of_parallelism,
                        is_beginning_of_section=not text.chapters[0]
                        .lines[0]
                        .is_beginning_of_section,
                    ),
                ),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )

    body = {"lines": create_dto(updated_text)["chapters"][0]["lines"]}
    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/lines", body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_dto(updated_text)

    get_result = client.simulate_get(
        f"/texts/{updated_text.category}/{updated_text.index}"
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_dto(updated_text)


def test_updating_text_not_found(client, bibliography):
    post_result = client.simulate_post(
        "/texts/1/1/chapters/0/lines", body=json.dumps({"lines": []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_text_category(client):
    post_result = client.simulate_post(
        "/texts/invalid/1/chapters/0/lines", body=json.dumps({"lines": []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_id(client):
    post_result = client.simulate_post(
        "/texts/1/invalid/chapters/0/lines", body=json.dumps({"lines": []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_chapter_index(client):
    post_result = client.simulate_post(
        "/texts/1/1/chapters/invalid/lines", body=json.dumps({"lines": []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


TOO_MANY_NOTES = {
    **ApiLineSchema().dump(TextFactory.build().chapters[0].lines[0]),
    "reconstruction": "kur\n#note: extra note\n#note: extra note",
}


@pytest.mark.parametrize(
    "lines,expected_status",
    [[[{}], falcon.HTTP_BAD_REQUEST], [[TOO_MANY_NOTES], falcon.HTTP_BAD_REQUEST]],
)
def test_update_invalid_entity(
    client, bibliography, lines, expected_status, sign_repository, signs
):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/lines",
        body=json.dumps({"lines": lines}),
    )

    assert post_result.status == expected_status


def test_importing(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    next_line_mumber = (
        cast(
            TextLine, text.chapters[0].lines[0].variants[0].manuscripts[0].line
        ).line_number.number
        + 1
    )
    atf = (
        f"{text.chapters[0].lines[0].number.number+1}. bu\n"
        f"{str(text.chapters[0].manuscripts[0].siglum)} {next_line_mumber}. ..."
    )

    updated_text = attr.evolve(
        text,
        chapters=(
            attr.evolve(
                text.chapters[0],
                lines=(
                    *text.chapters[0].lines,
                    *parse_chapter(atf, text.chapters[0].manuscripts),
                ),
                signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\n\nKU",),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )

    body = {"atf": atf}
    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/import", body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_dto(updated_text)

    get_result = client.simulate_get(
        f"/texts/{updated_text.category}/{updated_text.index}"
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_dto(updated_text)


@pytest.mark.parametrize(
    "body,expected_status",
    [
        [{}, falcon.HTTP_BAD_REQUEST],
        [{"atf": ""}, falcon.HTTP_UNPROCESSABLE_ENTITY],
        [{"atf": "invalid atf"}, falcon.HTTP_UNPROCESSABLE_ENTITY],
    ],
)
def test_import_invalid_entity(
    client, bibliography, body, expected_status, sign_repository, signs
):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/import", body=json.dumps(body)
    )

    assert post_result.status == expected_status
