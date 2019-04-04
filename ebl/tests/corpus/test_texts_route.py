import falcon
from ebl.tests.factories.corpus import TextFactory


def test_get_text(client, corpus):
    text = TextFactory.build()
    corpus.create(text)
    result = client.simulate_get(f'/texts/{text.category}/{text.index}')

    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'
    assert result.json == text.to_dict()


def test_text_not_found(client):
    result = client.simulate_get('/texts/1/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_section(client):
    result = client.simulate_get('/texts/invalid/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_index(client):
    result = client.simulate_get('/texts/1/invalid')

    assert result.status == falcon.HTTP_NOT_FOUND
