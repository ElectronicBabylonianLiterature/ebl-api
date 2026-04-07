import falcon

from ebl.provenance.application.provenance_schema import ApiProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import STANDARD_TEXT_PROVENANCE_ID
from ebl.provenance.web.provenances import _sort_key
from ebl.tests.factories.provenance import build_provenance_records


def test_get_provenance(client):
    get_result = client.simulate_get("/provenances")
    assert get_result.status == falcon.HTTP_OK
    filtered = [
        r for r in build_provenance_records() if r.id != STANDARD_TEXT_PROVENANCE_ID
    ]
    parents = sorted([r for r in filtered if r.parent is None], key=_sort_key)
    children = sorted([r for r in filtered if r.parent is not None], key=_sort_key)
    expected_payload = ApiProvenanceRecordSchema(many=True).dump([*parents, *children])
    assert get_result.json == expected_payload
