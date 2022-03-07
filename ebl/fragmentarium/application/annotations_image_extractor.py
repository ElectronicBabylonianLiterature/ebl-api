from typing import Sequence

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.domain.annotation import CroppedAnnotationImage
from ebl.fragmentarium.domain.museum_number import MuseumNumber
import attr


@attr.attrs(auto_attribs=True, frozen=True)
class CroppedAnnotation(CroppedAnnotationImage):
    fragment_number: MuseumNumber


class AnnotationCroppedImageService:
    def __init__(
        self,
        annotations_repository: AnnotationsRepository,
    ):
        self._annotations_repository = annotations_repository

    def find_annotations_by_sign(self, sign: str) -> Sequence[CroppedAnnotation]:
        annotations = self._annotations_repository.find_by_sign(sign)
        cropped_image_annotations = []
        for annotation in annotations:
            for annotation_elem in annotation.annotations:
                image = annotation_elem.image
                if image:
                    cropped_image_annotations.append(
                        CroppedAnnotation(
                            image.image,
                            image.script,
                            image.label,
                            annotation.fragment_number,
                        )
                    )
        return cropped_image_annotations
