import falcon

from ebl.fragmentarium.domain.genres import genres


def test_get_genre(client):
    get_result = client.simulate_get("/genres")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == list(map(list, genres))
