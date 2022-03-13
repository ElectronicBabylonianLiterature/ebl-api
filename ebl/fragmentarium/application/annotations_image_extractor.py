from typing import Sequence

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.cropped_sign_image import Base64
from ebl.fragmentarium.application.sign_images_repository import SignImagesRepository
from ebl.fragmentarium.domain.annotation import CroppedAnnotationImage
from ebl.fragmentarium.domain.museum_number import MuseumNumber
import attr


@attr.attrs(auto_attribs=True, frozen=True)
class CroppedAnnotation(CroppedAnnotationImage):
    fragment_number: MuseumNumber
    image: Base64


class AnnotationCroppedImageService:
    def __init__(
        self,
        annotations_repository: AnnotationsRepository,
        sign_images_repository: SignImagesRepository,
    ):
        self._annotations_repository = annotations_repository
        self._sign_repository = sign_images_repository

    def find_annotations_by_sign(self, sign: str) -> Sequence[CroppedAnnotation]:
        annotations = self._annotations_repository.find_by_sign(sign)
        cropped_image_annotations = []
        for annotation in annotations:
            for annotation_elem in annotation.annotations:
                cropped_ann = annotation_elem.image
                if cropped_ann:
                    image = self._sign_repository.query_by_id(cropped_ann.image_id)

                    cropped_image_annotations.append(
                        CroppedAnnotation(cropped_ann.image.image_id)
                    )
        return cropped_image_annotations
