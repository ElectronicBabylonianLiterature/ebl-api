import json

import falcon

from ebl.auth0 import Guest
from ebl.corpus.web.api_serializer import deserialize, serialize
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (ChapterFactory, ManuscriptFactory,
                                        TextFactory)

ANY_USER = Guest()


def create_dto(text, include_documents=False):
    return serialize(text, include_documents)


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_text(client, text):
    post_result = client.simulate_post(
        f'/texts',
        body=json.dumps(create_dto(text))
    )
    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers['Location'] ==\
        f'/texts/{text.category}/{text.index}'
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == create_dto(text, True)


def test_parse_text():
    text = TextFactory.build(chapters=(
        ChapterFactory.build(manuscripts=(
            ManuscriptFactory.build(references=(
                ReferenceFactory.build(),
            )),
        )),
    ))
    dto = create_dto(text)

    assert deserialize(dto) == text


def test_to_dto():
    text = TextFactory.build()
    dto = create_dto(text, True)

    assert serialize(text) == dto


def test_created_text_can_be_fetched(client, bibliography, sign_repository,
                                     signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    get_result = client.simulate_get(f'/texts/{text.category}/{text.index}')

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == create_dto(text, True)


def test_text_not_found(client):
    result = client.simulate_get('/texts/1/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_section(client):
    result = client.simulate_get('/texts/invalid/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_index(client):
    result = client.simulate_get('/texts/1/invalid')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_listing_texts(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    first_text = TextFactory.build()
    second_text = TextFactory.build()
    allow_references(first_text, bibliography)
    allow_references(second_text, bibliography)
    create_text(client, first_text)
    create_text(client, second_text)

    get_result = client.simulate_get(f'/texts')

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == [
        {**dto, 'chapters': []}
        for dto
        in [
            create_dto(first_text, False),
            create_dto(second_text, False)
        ]
    ]
