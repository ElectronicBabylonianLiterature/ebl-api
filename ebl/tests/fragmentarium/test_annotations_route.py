import json

import falcon
from mockito import when

from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.annotation import AnnotationsFactory
from ebl.fragmentarium.application.annotations_service import AnnotationsService


def test_find_annotations(client):
    fragment_number = MuseumNumber("X", "2")
    annotations = Annotations(fragment_number)

    result = client.simulate_get(
        f"/fragments/{fragment_number}/annotations",
        params={"generateAnnotations": False},
    )

    expected_json = AnnotationsSchema().dump(annotations)
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.json == expected_json


def test_generate_annotations(client):
    fragment_number = MuseumNumber("X", "2")
    annotations = Annotations(fragment_number)

    when(AnnotationsService).generate_annotations(fragment_number).thenReturn(
        annotations
    )

    result = client.simulate_get(
        f"/fragments/{fragment_number}/annotations",
        params={"generateAnnotations": True},
    )

    expected_json = AnnotationsSchema().dump(annotations)
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.json == expected_json


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
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
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
