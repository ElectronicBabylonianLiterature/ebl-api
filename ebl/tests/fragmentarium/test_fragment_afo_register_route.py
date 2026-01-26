import falcon
import json
from ebl.tests.factories.fragment import (
    FragmentFactory,
)
from ebl.tests.factories.afo_register import AfoRegisterRecordFactory


def test_query_fragmentarium_afo_register(fragment_repository, client):
    record = AfoRegisterRecordFactory.build()
    record_id = f"{record.text} {record.text_number}"
    fragment = FragmentFactory.build(traditional_references=[record_id])
    fragment_repository.create_many([fragment, FragmentFactory.build()])

    post_result = client.simulate_post(
        "/fragments/query-by-traditional-references",
        body=json.dumps({"traditionalReferences": [record_id]}),
    )

    expected_json = {
        "items": [
            {
                "traditionalReference": record_id,
                "fragmentNumbers": [str(fragment.number)],
            }
        ]
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json
