import falcon

from ebl.common.application.provenance_schema import ApiProvenanceRecordSchema
from ebl.tests.factories.provenance import DEFAULT_PROVENANCES


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    assert get_result.status == falcon.HTTP_OK
    ids = {record["id"] for record in get_result.json}
    expected_ids = {record.id for record in DEFAULT_PROVENANCES}
    assert ids == expected_ids
    expected_payload = ApiProvenanceRecordSchema(many=True).dump(DEFAULT_PROVENANCES)
    assert get_result.json == expected_payload
