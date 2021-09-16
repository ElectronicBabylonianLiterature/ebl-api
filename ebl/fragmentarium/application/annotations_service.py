import os
from io import BytesIO

import requests
from PIL import Image

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations, BoundingBoxPrediction
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


class AnnotationsService:
    def __init__(
        self,
        annotations_repository: AnnotationsRepository,
        photo_repository: FileRepository,
        changelog,
    ):
        self._repository = annotations_repository
        self._photo_repository = photo_repository
        self._changelog = changelog

    def generate_annotations(
        self, number: MuseumNumber, threshold: float = 0.2
    ) -> Annotations:
        fragment_image = self._photo_repository.query_by_file_name(f"{number}.jpg")
        image_bytes = fragment_image.read()
        buf = BytesIO(image_bytes)
        width, height = Image.open(buf).size
        res = requests.post(
            f"{os.environ['EBL_AI_API']}/generate",
            data=buf.getvalue(),
            headers={"content-type": "image/png"},
        )

        if res.status_code == 200:
            boundary_results = res.json()
            bounding_boxes_predictions = list(
                map(
                    BoundingBoxPrediction.from_dict,
                    boundary_results["boundaryResults"],
                )
            )
            bounding_boxes_predictions = list(
                filter(
                    lambda bbox: bbox.probability >= threshold,
                    bounding_boxes_predictions,
                )
            )
            return Annotations.from_bounding_boxes_predictions(
                number, bounding_boxes_predictions, height, width
            )
        else:
            raise Exception("ebl-ai error")

    def find(self, number: MuseumNumber) -> Annotations:
        return self._repository.query_by_museum_number(number)

    def update(self, annotations: Annotations, user: User) -> Annotations:
        old_annotations = self._repository.query_by_museum_number(
            annotations.fragment_number
        )
        _id = str(annotations.fragment_number)
        schema = AnnotationsSchema()
        self._changelog.create(
            "annotations",
            user.profile,
            {"_id": _id, **schema.dump(old_annotations)},
            {"_id": _id, **schema.dump(annotations)},
        )
        self._repository.create_or_update(annotations)
        return annotations
