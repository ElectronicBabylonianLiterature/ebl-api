from typing import Sequence

import attr

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.domain.annotation import AnnotationValueType


class CroppedAnnotationService:
    def __init__(
        self,
        annotations_repository: AnnotationsRepository,
        cropped_sign_images_repository: CroppedSignImagesRepository,
        fragment_repository: FragmentRepository,
    ):
        self._annotations_repository = annotations_repository
        self._fragment_repository = fragment_repository
        self._cropped_sign_image_repository = cropped_sign_images_repository

    def find_annotations_by_sign(self, sign: str) -> Sequence[dict]:
        annotations = self._annotations_repository.find_by_sign(sign)
        cropped_image_annotations = []
        for annotation in annotations:
            date = DateSchema().dump(
                self._fragment_repository.fetch_date(annotation.fragment_number)
            )
            annotation = attr.evolve(
                annotation,
                annotations=[
                    x
                    for x in annotation.annotations
                    if x.data.type == AnnotationValueType.HAS_SIGN
                ],
            )
            for annotation_elem in annotation.annotations:
                if cropped_sign := annotation_elem.cropped_sign:
                    cropped_sign_image = (
                        self._cropped_sign_image_repository.query_by_id(
                            cropped_sign.image_id
                        )
                    )
                    cropped_image_annotations.append(
                        {
                            "fragmentNumber": str(annotation.fragment_number),
                            "image": cropped_sign_image.image,
                            "script": str(annotation.script),
                            "label": cropped_sign.label,
                            "date": date,
                            "provenance": annotation.provenance,
                        }
                    )
        return cropped_image_annotations
