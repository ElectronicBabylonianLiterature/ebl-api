from typing import Sequence

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)


class CroppedAnnotationService:
    def __init__(
        self,
        annotations_repository: AnnotationsRepository,
        cropped_sign_images_repository: CroppedSignImagesRepository,
    ):
        self._annotations_repository = annotations_repository
        self._cropped_sign_image_repository = cropped_sign_images_repository

    def find_annotations_by_sign(self, sign: str) -> Sequence[dict]:
        annotations = self._annotations_repository.find_by_sign(sign)
        cropped_image_annotations = []
        for annotation in annotations:
            for annotation_elem in annotation.annotations:
                cropped_sign = annotation_elem.cropped_sign
                if cropped_sign:
                    cropped_sign_image = (
                        self._cropped_sign_image_repository.query_by_id(
                            cropped_sign.image_id
                        )
                    )
                    cropped_image_annotations.append(
                        {
                            "fragmentNumber": annotation.fragment_number,
                            "image": cropped_sign_image.image,
                            "script": annotation.script,
                            "label": cropped_sign.label,
                        }
                    )
        return cropped_image_annotations
