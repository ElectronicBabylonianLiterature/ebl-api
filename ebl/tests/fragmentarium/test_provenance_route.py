import falcon

from ebl.provenance.application.provenance_schema import ApiProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import STANDARD_TEXT_PROVENANCE_ID
from ebl.tests.factories.provenance import build_provenance_records


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    assert get_result.status == falcon.HTTP_OK
    expected_records = sorted(
        (r for r in build_provenance_records() if r.id != STANDARD_TEXT_PROVENANCE_ID),
        key=lambda r: r.long_name,
    )
    expected_payload = ApiProvenanceRecordSchema(many=True).dump(expected_records)
    assert get_result.json == expected_payload
