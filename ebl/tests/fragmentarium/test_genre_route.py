import falcon  # pyre-ignore[21]

from ebl.fragmentarium.domain.genres import genres


def test_get_genre(client):
    get_result = client.simulate_get("/genre")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == list(map(list, genres))
