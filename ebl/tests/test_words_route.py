# pylint: disable=W0621
import json
from urllib import parse
import falcon
import pytest


@pytest.fixture
def saved_word(dictionary, word):
    word = {**word}
    dictionary.create(word)
    return word


def test_get_word(client, saved_word):
    object_id = saved_word['_id']
    result = client.simulate_get(f'/words/{object_id}')

    assert result.json == saved_word
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_word_not_found(client):
    object_id = 'not found'
    result = client.simulate_get(f'/words/{object_id}')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_word_invalid_id(client):
    object_id = 'invalid object id'
    result = client.simulate_get(f'/words/{object_id}')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_search_word(client, saved_word):
    lemma = parse.quote_plus(' '.join(saved_word['lemma']))
    result = client.simulate_get(f'/words', params={'query': lemma})

    assert result.json == [saved_word]
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_word_lemma(client, saved_word):
    lemma = parse.quote_plus(saved_word['lemma'][0][:2])
    result = client.simulate_get(f'/words', params={'lemma': lemma})

    assert result.status == falcon.HTTP_OK
    assert result.json == [saved_word]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_word_no_query(client):
    result = client.simulate_get(f'/words')

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_word_invalid_query(client):
    result = client.simulate_get(f'/words', params={'invalid': 'lemma'})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_word_double_query(client):
    result = client.simulate_get(
        f'/words', params={'query': 'lemma', 'lemma': 'lemma'}
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_update_word(client, saved_word, user, database):
    object_id = saved_word['_id']
    updated_word = {
        **saved_word,
        '_id': object_id,
        'lemma': ['new']
    }
    body = json.dumps(updated_word)
    post_result = client.simulate_post(f'/words/{object_id}', body=body)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'

    get_result = client.simulate_get(f'/words/{object_id}')

    assert get_result.json == updated_word
    assert database['changelog'].find_one({
        'resource_id': saved_word['_id'],
        'resource_type': 'words',
        'user_profile.name': user.profile['name']
    })


def test_update_word_not_found(client, word):
    object_id = 'not found'
    not_found_word = {
        **word,
        '_id': object_id
    }
    body = json.dumps(not_found_word)

    post_result = client.simulate_post(f'/words/{object_id}', body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_invalid_object_id(client, word):
    object_id = 'invalid object id'
    not_found_word = {
        **word,
        '_id': object_id
    }
    body = json.dumps(not_found_word)
    post_result = client.simulate_post(f'/words/{object_id}', body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_word_invalid_entity(client, saved_word):
    object_id = saved_word['_id']
    invalid_word = {
        **saved_word,
        '_id': object_id,
        'lemma': 'invalid'
    }
    body = json.dumps(invalid_word)

    post_result = client.simulate_post(f'/words/{object_id}', body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST
