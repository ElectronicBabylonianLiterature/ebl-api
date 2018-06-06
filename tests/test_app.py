import json
import pytest

import falcon
from falcon import testing
from falcon_auth import NoneAuthBackend

from bson.json_util import dumps

import mongomock

import dictionary.app
from dictionary.dictionary import MongoDictionary


@pytest.fixture
def mongo_dictionary():
    mongo_dictionary = MongoDictionary(mongomock.MongoClient())
    return mongo_dictionary

@pytest.fixture
def client(mongo_dictionary):
    user_loader = lambda: {}
    auth_backend = NoneAuthBackend(user_loader)

    api = dictionary.app.create_app(mongo_dictionary, auth_backend)
    return testing.TestClient(api)

@pytest.fixture
def word(mongo_dictionary):
    word = {
        'lemma': ['part1', 'part2'],
        'homonym':  'I'
    }
    mongo_dictionary.create(word)
    return word

def test_get_word(client, word):
    lemma = ' '.join(word['lemma'])
    homonym = word['homonym']
    result = client.simulate_get(f'/words/{lemma}/{homonym}')

    assert json.loads(result.content) == dumps(word)
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'

def test_lemma_not_found(client):
    result = client.simulate_get(f'/words/unknown/I')

    assert result.status == falcon.HTTP_NOT_FOUND

def test_homonym_not_found(client):
    result = client.simulate_get(f'/words/part1 part2/II')

    assert result.status == falcon.HTTP_NOT_FOUND

def test_cors(client):
    headers = {'Access-Control-Request-Method': 'GET'}
    result = client.simulate_options(f'/words/part1 part2/I', headers=headers)

    assert result.headers['Access-Control-Allow-Methods'] == 'GET'
    assert result.headers['Access-Control-Allow-Origin'] == '*'
    assert result.headers['Access-Control-Max-Age'] == '86400'
