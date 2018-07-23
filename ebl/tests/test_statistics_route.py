# pylint: disable=W0621
import json
import falcon


def test_get_statistics(client):
    result = client.simulate_get('/statistics')

    assert json.loads(result.content) == {
        'transliteratedFragments': 0,
        'lines': 0
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'
