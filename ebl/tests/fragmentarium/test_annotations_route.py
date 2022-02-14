import json

import falcon
import httpretty

from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.annotation import AnnotationsFactory


def test_find_annotations(client):
    fragment_number = MuseumNumber("X", "2")
    annotations = Annotations(fragment_number)

    result = client.simulate_get(
        f"/fragments/{fragment_number}/annotations",
        params={"generateAnnotations": False},
    )

    expected_json = AnnotationsSchema().dump(annotations)
    assert result.status == falcon.HTTP_OK
    assert result.json == expected_json


@httpretty.activate
def test_generate_annotations(client, photo_repository):
    fragment_number = MuseumNumber.of("K.2")

    boundary_results = {
        "boundaryResults": [
            {
                "top_left_x": 0.0,
                "top_left_y": 0.0,
                "width": 10.0,
                "height": 10.0,
                "probability": 0.99,
            }
        ]
    }
    httpretty.register_uri(
        httpretty.POST,
        "http://localhost:8001/generate",
        body=json.dumps(boundary_results),
        content_type="image/jpeg",
    )

    result = client.simulate_get(
        f"/fragments/{fragment_number}/annotations",
        params={"generateAnnotations": True},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json is not None
    assert result.json["fragmentNumber"] == "K.2"
    assert result.json["annotations"][0]["geometry"]["x"] == 0.0
    assert result.json["annotations"][0]["geometry"]["y"] == 0.0


def test_find_not_allowed(guest_client):
    result = guest_client.simulate_get(
        "/fragments/X.1/annotations", params={"generateAnnotations": False}
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_update(client):
    annotations = AnnotationsFactory.build()
    fragment_number = annotations.fragment_number
    body = AnnotationsSchema().dumps(annotations)
    url = f"/fragments/{fragment_number}/annotations"
    post_result = client.simulate_post(url, body=body)

    expected_json = AnnotationsSchema().dump(annotations)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(
        f"/fragments/{fragment_number}/annotations",
        params={"generateAnnotations": False},
    )
    assert get_result.json == expected_json


def test_update_number_mismatch(client):
    annotations = AnnotationsFactory.build()
    body = AnnotationsSchema().dumps(annotations)
    url = "/fragments/not.match/annotations"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_update_invalid_number(client):
    annotations = AnnotationsFactory.build()
    body = AnnotationsSchema().dumps(annotations)
    url = "/fragments/invalid/annotations"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_update_invalid(client):
    body = json.dumps({"thisIs": "invalid annotations", "fragmentNumber": "X.1"})
    url = "/fragments/X.1/annotations"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_update_not_allowed(guest_client):
    annotations = AnnotationsFactory.build()
    body = AnnotationsSchema().dumps(annotations)
    url = "/fragments/not match/annotations"
    result = guest_client.simulate_post(url, body=body)

    assert result.status == falcon.HTTP_FORBIDDEN
