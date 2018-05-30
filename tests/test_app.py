import falcon
import json
from falcon import testing
import pytest

import dictionary.app


@pytest.fixture
def client():
    api = dictionary.app.create_app('./tests/dictionary.json')
    return testing.TestClient(api)

def test_get_word(client):
    part1 = 'part1'
    part2 = 'part2'
    homonym = 'I'

    expectedWord = {
        'lemma': [part1, part2],
        'homonym': homonym
    }

    result = client.simulate_get(f'/words/{part1} {part2}/{homonym}')
 
    assert json.loads(result.content) == expectedWord
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'

def test_lemma_not_found(client):
    result = client.simulate_get(f'/words/unknown/I')
 
    assert result.status == falcon.HTTP_NOT_FOUND

def test_homonym_not_found(client):
    result = client.simulate_get(f'/words/part1 part2/II')
 
    assert result.status == falcon.HTTP_NOT_FOUND

def test_cors(client):
    result = client.simulate_options(f'/words/part1 part2/I', headers={'Access-Control-Request-Method': 'GET'})
    assert result.headers['Access-Control-Allow-Methods'] == 'GET'
    assert result.headers['Access-Control-Allow-Origin'] == '*'
    assert result.headers['Access-Control-Max-Age'] == '86400'
    