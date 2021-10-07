from io import BytesIO
from typing import List

import requests
from PIL import Image

from ebl.files.application.file_repository import File
from ebl.fragmentarium.domain.annotation import Annotations, BoundingBoxPrediction
from ebl.fragmentarium.domain.museum_number import MuseumNumber


class EblAiClient:
    api_url: str

    def __init__(self, api_url: str):
        self.api_url = api_url

    def request_generate_annotations(self, data: bytes) -> List[dict]:
        generate_endpoint = f"{self.api_url}/generate"

        res = requests.post(
            generate_endpoint, data=data, headers={"content-type": "image/png"}
        )
        if res.status_code != 200:
            raise Exception("ebl-ai error")
        else:
            return res.json()["boundaryResults"]

    def generate_annotations(
        self, number: MuseumNumber, fragment_image: File, threshold: float = 0.3
    ) -> Annotations:
        image_bytes = fragment_image.read()
        buf = BytesIO(image_bytes)
        width, height = Image.open(buf).size
        boundary_results = self.request_generate_annotations(buf.getvalue())

        bounding_boxes_predictions = list(
            map(BoundingBoxPrediction.from_dict, boundary_results)
        )
        bounding_boxes_predictions = list(
            filter(
                lambda bbox: bbox.probability >= threshold, bounding_boxes_predictions
            )
        )
        return Annotations.from_bounding_boxes_predictions(
            number, bounding_boxes_predictions, height, width
        )
