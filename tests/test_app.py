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

    response = client.simulate_get(f'/words/{part1} {part2}/{homonym}')
 
    assert json.loads(response.content) == expectedWord
    assert response.status == falcon.HTTP_OK

def test_lemma_not_found(client):
    response = client.simulate_get(f'/words/unknown/I')
 
    assert response.status == falcon.HTTP_NOT_FOUND

def test_homonym_not_found(client):
    response = client.simulate_get(f'/words/part1 part2/II')
 
    assert response.status == falcon.HTTP_NOT_FOUND
    