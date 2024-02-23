import falcon

from ebl.corpus.domain.provenance import Provenance


def test_get_genre(client):
    get_result = client.simulate_get("/provenances")
    provenances_data = tuple((prov.long_name, prov.parent) for prov in Provenance)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == list(map(list, provenances_data))
