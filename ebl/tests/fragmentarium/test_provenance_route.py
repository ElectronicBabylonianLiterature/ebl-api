import falcon

from ebl.provenance.application.provenance_schema import ApiProvenanceRecordSchema
from ebl.tests.factories.provenance import build_provenance_records


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    assert get_result.status == falcon.HTTP_OK
    expected_records = build_provenance_records()
    expected_payload = ApiProvenanceRecordSchema(many=True).dump(expected_records)
    assert get_result.json == expected_payload
