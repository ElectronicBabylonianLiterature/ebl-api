import falcon
import json
from falcon import testing
import pytest

from dictionary.app import api


@pytest.fixture
def client():
    return testing.TestClient(api)

def test_list_images(client):
    entry = {
        'lemma': ['abā\'u']
    }

    response = client.simulate_get('/')

    assert json.loads(response.content) == entry
    assert response.status == falcon.HTTP_OK
    