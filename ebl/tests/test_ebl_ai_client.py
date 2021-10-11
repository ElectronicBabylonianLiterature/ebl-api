import io

import pytest
import requests
from PIL import Image
from mockito import mock

from ebl.ebl_ai_client import EblAiClient, BoundingBoxPredictionSchema, EblAiApiError
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import BoundingBoxPrediction
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.conftest import FakeFile

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


def test_generate_annotations(
    annotations_repository, photo_repository, changelog, when
):
    fragment_number = MuseumNumber.of("X.0")
    image = Image.open("ebl/tests/fragmentarium/test_image.jpeg")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()
    image_file = FakeFile(str(fragment_number), raw_bytes, {})

    ebl_ai_client = EblAiClient("mock-localhost:8001")
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

    when(requests).post(
        "mock-localhost:8001/generate",
        data=raw_bytes,
        headers={"content-type": "image/png"},
    ).thenReturn(mock({"json": lambda: boundary_results, "status_code": 200}))

    annotations = ebl_ai_client.generate_annotations(fragment_number, image_file)
    assert annotations.fragment_number == fragment_number
    assert len(annotations.annotations) == 1
    assert annotations.annotations[0].geometry.x == 0.0
    assert annotations.annotations[0].geometry.y == 0.0


def test_generate_annotations_error(
    annotations_repository, photo_repository, changelog, when
):
    fragment_number = MuseumNumber.of("X.0")
    image = Image.open("ebl/tests/fragmentarium/test_image.jpeg")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()
    image_file = FakeFile(str(fragment_number), raw_bytes, {})

    ebl_ai_client = EblAiClient("mock-localhost:8001")

    when(requests).post(
        "mock-localhost:8001/generate",
        data=raw_bytes,
        headers={"content-type": "image/png"},
    ).thenReturn(mock({"status_code": 400}))
    with pytest.raises(EblAiApiError):
        ebl_ai_client.generate_annotations(fragment_number, image_file)
