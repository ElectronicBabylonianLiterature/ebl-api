import falcon
import httpretty
import pytest


@pytest.mark.parametrize('status,has_photo', [
    (200, True),
    (404, False)
])
@httpretty.activate
def test_get(status, has_photo, client):
    number = 'P397611'
    url = f'https://cdli.ucla.edu/dl/photo/{number}.jpg'

    httpretty.register_uri(httpretty.HEAD, url, status=status)
    result = client.simulate_get(f'/cdli/{number}')

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        'photoUrl': url if has_photo else None
    }
    assert result.headers['Access-Control-Allow-Origin'] == '*'
