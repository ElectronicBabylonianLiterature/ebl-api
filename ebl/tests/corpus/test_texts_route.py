import json
import attr
import falcon
import pytest
from ebl.tests.factories.corpus import (
    TextFactory, ChapterFactory, ManuscriptFactory
)


def put_text(client, text):
    put_result = client.simulate_put(
        f'/texts',
        body=json.dumps(text.to_dict())
    )
    assert put_result.status == falcon.HTTP_NO_CONTENT
    assert put_result.headers['Access-Control-Allow-Origin'] == '*'


def test_created_text_can_be_fetched(client):
    text = TextFactory.build()
    put_text(client, text)

    get_result = client.simulate_get(f'/texts/{text.category}/{text.index}')

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == text.to_dict()


def test_text_not_found(client):
    result = client.simulate_get('/texts/1/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_section(client):
    result = client.simulate_get('/texts/invalid/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_index(client):
    result = client.simulate_get('/texts/1/invalid')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_updating_text(client):
    text = TextFactory.build()
    updated_text = attr.evolve(text, index=2, name='New Name')

    put_text(client, text)
    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text.to_dict())
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == updated_text.to_dict()

    get_result = client.simulate_get(
        f'/texts/{updated_text.category}/{updated_text.index}'
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == updated_text.to_dict()


def test_updating_text_not_found(client):
    text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(text.to_dict())
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_text_invalid_category(client):
    text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/invalid/{text.index}',
        body=json.dumps(text.to_dict())
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_text_invalid_id(client):
    text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/{text.category}/invalid',
        body=json.dumps(text.to_dict())
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("updated_text,expected_status", [
    [TextFactory.build(category='invalid'), falcon.HTTP_BAD_REQUEST],
    [TextFactory.build(chapters=(
        ChapterFactory.build(manuscripts=(
            ManuscriptFactory.build(siglum='duplicate'),
            ManuscriptFactory.build(siglum='duplicate')
        )),
    )), falcon.HTTP_UNPROCESSABLE_ENTITY]
])
def test_update_transliteration_invalid_entity(client,
                                               updated_text,
                                               expected_status):
    text = TextFactory.build()
    put_text(client, text)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text.to_dict())
    )

    assert post_result.status == expected_status
