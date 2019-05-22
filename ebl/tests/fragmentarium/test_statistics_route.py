
import falcon


def test_get_statistics(guest_client):
    result = guest_client.simulate_get('/statistics')

    assert result.json == {
        'transliteratedFragments': 0,
        'lines': 0
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'
