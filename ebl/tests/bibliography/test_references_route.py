import json
import falcon
import pytest
from ebl.fragmentarium.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory


def test_update_references(client,
                           fragmentarium,
                           bibliography,
                           reference,
                           bibliography_entry,
                           user):
    # pylint: disable=R0913
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    bibliography.create(bibliography_entry, user)
    references = [reference.to_dict()]
    body = json.dumps({'references': references})
    url = f'/fragments/{fragment_number}/references'
    post_result = client.simulate_post(url, body=body)

    expected_json = create_response_dto(
        fragment.set_references((reference,)),
        user
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == expected_json

    get_result = client.simulate_get(f'/fragments/{fragment_number}')
    assert get_result.json == expected_json


def test_update_references_not_found(client):
    url = '/fragments/unknown.fragment/references'
    body = json.dumps({'references': []})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("body", [
    '"reference"',
    json.dumps([{'id': 'id', 'type': 'EDITION'}]),
    json.dumps({'references': [
        {'id': 'id',
         'type': 'WRONG',
         'pages': '',
         'notes': '',
         'linesCited': []}
    ]}),
    json.dumps({'references': [
        {'type': 'EDITION', 'pages': '', 'notes': '', 'linesCited': []}
    ]})
])
def test_update_references_invalid_reference(client,
                                             fragmentarium,
                                             body):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    url = f'/fragments/{fragment_number}/references'

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_update_references_invalid_id(client,
                                      fragmentarium,
                                      reference):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    body = json.dumps({'references': [reference.to_dict()]})
    url = f'/fragments/{fragment_number}/references'
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
