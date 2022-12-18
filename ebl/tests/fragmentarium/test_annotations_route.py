import json

import falcon
import httpretty

from ebl.fragmentarium.application.annotations_schema import AnnotationsWithScriptSchema
from ebl.fragmentarium.domain.annotation import Annotations

from ebl.tests.conftest import create_test_photo
from ebl.tests.factories.annotation import AnnotationsFactory, AnnotationFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_find_annotations(client):
    fragment_number = MuseumNumber("X", "2")
    annotations = Annotations(fragment_number)

    result = client.simulate_get(
        f"/fragments/{fragment_number}/annotations",
        params={"generateAnnotations": False},
    )

    expected_json = AnnotationsWithScriptSchema().dump(annotations)
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


def test_update(client, fragment_repository, photo_repository):
    number = MuseumNumber.of("K.123")
    annotation_1 = AnnotationFactory(cropped_sign=None)
    annotation_2 = AnnotationFactory(cropped_sign=None)
    annotations = AnnotationsFactory.build(
        fragment_number=number, annotations=[annotation_1, annotation_2]
    )
    fragment = TransliteratedFragmentFactory.build(number=number)
    fragment_repository.create(fragment)
    photo_repository._create(create_test_photo(number))

    body = AnnotationsWithScriptSchema().dump(annotations)
    url = f"/fragments/{number}/annotations"
    post_result = client.simulate_post(url, body=json.dumps(body))

    expected_json = AnnotationsWithScriptSchema().dump(annotations)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json["fragmentNumber"] == expected_json["fragmentNumber"]
    for annotation, expected_annotation in zip(
        post_result.json["annotations"], expected_json["annotations"]
    ):
        assert annotation["geometry"] == expected_annotation["geometry"]
        assert annotation["data"] == expected_annotation["data"]
        assert annotation["croppedSign"] is not None

    get_result = client.simulate_get(
        f"/fragments/{number}/annotations",
        params={"generateAnnotations": False},
    )
    assert get_result.json == post_result.json


def test_update_number_mismatch(client):
    annotations = AnnotationsFactory.build()
    body = AnnotationsWithScriptSchema().dumps(annotations)
    url = "/fragments/not.match/annotations"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_update_invalid_number(client):
    annotations = AnnotationsFactory.build()
    body = AnnotationsWithScriptSchema().dumps(annotations)
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
    body = AnnotationsWithScriptSchema().dumps(annotations)
    url = "/fragments/not match/annotations"
    result = guest_client.simulate_post(url, body=body)

    assert result.status == falcon.HTTP_FORBIDDEN
