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
    unique_lemma = saved_word['_id']
    result = client.simulate_get(f'/words/{unique_lemma}')

    assert result.json == saved_word
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_word_not_found(client):
    unique_lemma = 'not found'
    result = client.simulate_get(f'/words/{unique_lemma}')

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


@pytest.mark.parametrize("transform", [
    lambda word: word,
    lambda word: {**word, 'derived': []}
])
def test_update_word(transform, client, saved_word, user, database):
    unique_lemma = saved_word['_id']
    updated_word = transform(saved_word)
    body = json.dumps(updated_word)
    post_result = client.simulate_post(f'/words/{unique_lemma}', body=body)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'

    get_result = client.simulate_get(f'/words/{unique_lemma}')

    assert get_result.json == updated_word
    assert database['changelog'].find_one({
        'resource_id': unique_lemma,
        'resource_type': 'words',
        'user_profile.name': user.profile['name']
    })


def test_update_word_not_found(client, word):
    unique_lemma = 'not found'
    not_found_word = {
        **word,
        '_id': unique_lemma
    }
    body = json.dumps(not_found_word)

    post_result = client.simulate_post(f'/words/{unique_lemma}', body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("transform", [
    lambda word: {**word, 'lemma': []},
    lambda word: {**word, 'derived': [[]]}
])
def test_update_word_invalid_entity(transform, client, saved_word):
    unique_lemma = saved_word['_id']
    invalid_word = transform(saved_word)
    body = json.dumps(invalid_word)

    post_result = client.simulate_post(f'/words/{unique_lemma}', body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST
