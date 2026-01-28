from io import BytesIO
from typing import List

import requests
from PIL import Image
from marshmallow import Schema, fields, post_load

from ebl.files.application.file_repository import File
from ebl.fragmentarium.domain.annotation import Annotations, BoundingBoxPrediction
from ebl.transliteration.domain.museum_number import MuseumNumber


class EblAiApiError(Exception):
    pass


class BoundingBoxPredictionSchema(Schema):
    top_left_x = fields.Float(required=True)
    top_left_y = fields.Float(required=True)
    width = fields.Float(required=True)
    height = fields.Float(required=True)
    probability = fields.Float(required=True)

    @post_load
    def make_line_number(self, data: dict, **kwargs) -> BoundingBoxPrediction:
        return BoundingBoxPrediction(
            data["top_left_x"],
            data["top_left_y"],
            data["width"],
            data["height"],
            data["probability"],
        )


class EblAiClient:
    api_url: str

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.generate_endpoint = f"{self.api_url}/generate"

    def _request_generate_annotations(self, data: bytes) -> List[BoundingBoxPrediction]:
        res = requests.post(
            self.generate_endpoint, data=data, headers={"content-type": "image/png"}
        )
        if res.status_code != 200:
            raise EblAiApiError(f"Ebl-Ai-Api Error with status code: {res.status_code}")
        else:
            return BoundingBoxPredictionSchema().load(
                res.json()["boundaryResults"], many=True
            )

    def generate_annotations(
        self, number: MuseumNumber, fragment_image: File, threshold: float = 0.3
    ) -> Annotations:
        image_bytes = fragment_image.read()
        buf = BytesIO(image_bytes)
        width, height = Image.open(buf).size
        bounding_boxes_predictions = self._request_generate_annotations(buf.getvalue())

        bounding_boxes_predictions = list(
            filter(
                lambda bbox: bbox.probability >= threshold, bounding_boxes_predictions
            )
        )
        return Annotations.from_bounding_boxes_predictions(
            number, bounding_boxes_predictions, height, width
        )
