import falcon

from ebl.tests.factories.provenance import build_provenance_records


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    assert get_result.status == falcon.HTTP_OK
    expected_records = build_provenance_records()
    expected_payload = [
        [
            record.long_name,
            record.parent if record.parent is None else f"[{record.parent}]",
        ]
        for record in expected_records
        if record.id != "STANDARD_TEXT"
    ]
    assert get_result.json == expected_payload
