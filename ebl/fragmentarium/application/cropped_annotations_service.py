from typing import Sequence

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.cropped_sign_image import CroppedAnnotation
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

    def find_annotations_by_sign(self, sign: str) -> Sequence[CroppedAnnotation]:
        annotations = self._annotations_repository.find_by_sign(sign)
        cropped_image_annotations = []
        for annotation in annotations:
            for annotation_elem in annotation.annotations:
                if cropped_sign := annotation_elem.cropped_sign:
                    cropped_sign_image = (
                        self._cropped_sign_image_repository.query_by_id(
                            cropped_sign.image_id
                        )
                    )
                    cropped_image_annotations.append(
                        CroppedAnnotation.from_cropped_sign(
                            annotation.fragment_number,
                            cropped_sign_image.image,
                            cropped_sign,
                        )
                    )
        return cropped_image_annotations
