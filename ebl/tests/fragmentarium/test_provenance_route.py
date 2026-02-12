import falcon

from ebl.common.domain.provenance import Provenance


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    provenances_data = tuple(
        (
            (prov.long_name, prov.parent)
            if prov.parent is None
            else (prov.long_name, f"[{prov.parent}]")
        )
        for prov in Provenance
        if prov.long_name != "Standard Text"
    )
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == list(map(list, provenances_data))
