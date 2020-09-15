import json

import falcon  # pyre-ignore
import pytest  # pyre-ignore

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.users.domain.user import Guest
from ebl.fragmentarium.domain.museum_number import MuseumNumber

ANY_USER = Guest()


def test_update_references(client, fragmentarium, bibliography, user):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    reference = ReferenceWithDocumentFactory.build()
    bibliography.create(reference.document, ANY_USER)
    references = [ReferenceSchema().dump(reference)]
    body = json.dumps({"references": references})
    url = f"/fragments/{fragment.number}/references"
    post_result = client.simulate_post(url, body=body)

    expected_json = create_response_dto(
        fragment.set_references((reference,)),
        user,
        fragment.number == MuseumNumber("K", "1"),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment.number}")
    assert get_result.json == expected_json


def test_update_references_not_found(client):
    url = "/fragments/unknown.fragment/references"
    body = json.dumps({"references": []})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_references_invalid_museum_number(client):
    url = "/fragments/invalid/references"
    body = json.dumps({"references": []})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "body",
    [
        '"reference"',
        json.dumps([{"id": "id", "type": "EDITION"}]),
        json.dumps(
            {
                "references": [
                    {
                        "id": "id",
                        "type": "WRONG",
                        "pages": "",
                        "notes": "",
                        "linesCited": [],
                    }
                ]
            }
        ),
        json.dumps(
            {
                "references": [
                    {"type": "EDITION", "pages": "", "notes": "", "linesCited": []}
                ]
            }
        ),
    ],
)
def test_update_references_invalid_reference(client, fragmentarium, body):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/references"

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_update_references_invalid_id(client, fragmentarium):
    reference = ReferenceWithDocumentFactory.build()
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    body = json.dumps({"references": [ReferenceSchema().dump(reference)]})
    url = f"/fragments/{fragment.number}/references"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
