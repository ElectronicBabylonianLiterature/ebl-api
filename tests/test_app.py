import json
from base64 import b64encode
import falcon
from falcon import testing
import pytest

import dictionary.app



@pytest.fixture
def client():
    api = dictionary.app.create_app('./tests/dictionary.json')
    return testing.TestClient(api)

@pytest.fixture 
def headers():
    userAndPass = b64encode(b"username:password").decode("ascii")
    return { 'Authorization' : f'Basic {userAndPass}'}

def test_get_word(client, headers):
    part1 = 'part1'
    part2 = 'part2'
    homonym = 'I'

    expected_word = {
        'lemma': [part1, part2],
        'homonym': homonym
    }

    result = client.simulate_get(f'/words/{part1} {part2}/{homonym}', headers=headers)

    assert json.loads(result.content) == expected_word
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'

def test_lemma_not_found(client, headers):
    result = client.simulate_get(f'/words/unknown/I', headers=headers)

    assert result.status == falcon.HTTP_NOT_FOUND

def test_homonym_not_found(client, headers):
    result = client.simulate_get(f'/words/part1 part2/II', headers=headers)

    assert result.status == falcon.HTTP_NOT_FOUND

def test_cors(client, headers):
    headers = {'Access-Control-Request-Method': 'GET'}
    result = client.simulate_options(f'/words/part1 part2/I', headers=headers)

    assert result.headers['Access-Control-Allow-Methods'] == 'GET'
    assert result.headers['Access-Control-Allow-Origin'] == '*'
    assert result.headers['Access-Control-Max-Age'] == '86400'

def test_unauthorized(client):
    result = client.simulate_get(f'/words/part1 part2/I')

    assert result.status == falcon.HTTP_UNAUTHORIZED
    