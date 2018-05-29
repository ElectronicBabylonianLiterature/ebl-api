import falcon
import json
from falcon import testing
import pytest

from dictionary.app import api


@pytest.fixture
def client():
    return testing.TestClient(api)

def test_list_images(client):
    part1 = 'part1'
    part2 = 'part2'
    entry = {
        'lemma': [part1, part2]
    }

    response = client.simulate_get(f'/{part1} {part2}')
 
    assert json.loads(response.content) == entry
    assert response.status == falcon.HTTP_OK
    