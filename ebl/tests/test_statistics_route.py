# pylint: disable=W0621
import falcon


def test_get_statistics(client):
    result = client.simulate_get('/statistics')

    assert result.json == {
        'transliteratedFragments': 0,
        'lines': 0
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'
