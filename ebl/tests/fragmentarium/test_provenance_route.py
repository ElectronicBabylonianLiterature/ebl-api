import falcon

from ebl.common.application.provenance_schema import ApiProvenanceRecordSchema
from ebl.common.domain.provenance_data import build_provenance_records


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    assert get_result.status == falcon.HTTP_OK
    ids = {record["id"] for record in get_result.json}
    expected_records = build_provenance_records()
    expected_ids = {record.id for record in expected_records}
    assert ids == expected_ids
    expected_payload = ApiProvenanceRecordSchema(many=True).dump(expected_records)
    assert get_result.json == expected_payload
