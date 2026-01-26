import json

import httpretty
import pytest

from ebl.ebl_ai_client import EblAiClient, BoundingBoxPredictionSchema, EblAiApiError
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import BoundingBoxPrediction
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.conftest import create_test_photo

SCHEMA = AnnotationsSchema()


def test_bounding_box_predition_schema():
    bbox_dict = {
        "top_left_x": 0.0,
        "top_left_y": 0.1,
        "width": 0.2,
        "height": 0.3,
        "probability": 0.4,
    }

    assert BoundingBoxPredictionSchema().load(bbox_dict) == BoundingBoxPrediction(
        0.0, 0.1, 0.2, 0.3, 0.4
    )


@httpretty.activate
def test_generate_annotations(
    annotations_repository, photo_repository, changelog, when
):
    fragment_number = MuseumNumber.of("X.0")

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
        "http://mock-localhost:8001/generate",
        body=json.dumps(boundary_results),
        content_type="image/jpeg",
    )

    image_file = create_test_photo(fragment_number)
    ebl_ai_client = EblAiClient("http://mock-localhost:8001")

    annotations = ebl_ai_client.generate_annotations(fragment_number, image_file)
    assert annotations.fragment_number == fragment_number
    assert len(annotations.annotations) == 1
    assert annotations.annotations[0].geometry.x == 0.0
    assert annotations.annotations[0].geometry.y == 0.0


@httpretty.activate
def test_generate_annotations_error(
    annotations_repository, photo_repository, changelog, when
):
    fragment_number = MuseumNumber.of("X.0")
    image_file = create_test_photo(fragment_number)

    ebl_ai_client = EblAiClient("http://localhost:8001")

    httpretty.register_uri(httpretty.POST, "http://localhost:8001/generate", status=404)

    with pytest.raises(EblAiApiError, match="Ebl-Ai-Api Error with status code: 404"):
        ebl_ai_client.generate_annotations(fragment_number, image_file)
