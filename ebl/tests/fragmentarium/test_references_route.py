import json

import falcon
import pytest

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.users.domain.user import Guest

ANY_USER = Guest()


def test_update_references(
    client, fragmentarium, bibliography, parallel_line_injector, user
):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    reference = ReferenceFactory.build(with_document=True)
    bibliography.create(reference.document, ANY_USER)
    references = [ReferenceSchema().dump(reference)]
    body = json.dumps({"references": references})
    url = f"/fragments/{fragment.number}/references"
    post_result = client.simulate_post(url, body=body)

    expected_json = create_response_dto(
        fragment.set_references((reference,)).set_text(
            parallel_line_injector.inject_transliteration(fragment.text)
        ),
        user,
        fragment.number == MuseumNumber("K", "1"),
    )

    assert post_result.status == falcon.HTTP_OK
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
    reference = ReferenceFactory.build(with_document=True)
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    body = json.dumps({"references": [ReferenceSchema().dump(reference)]})
    url = f"/fragments/{fragment.number}/references"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
