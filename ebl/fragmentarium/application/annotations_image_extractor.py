import base64
import io
from io import BytesIO
from typing import Sequence, NewType

import attr
from PIL import Image

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import BoundingBox, Annotation
from ebl.fragmentarium.domain.museum_number import MuseumNumber

Base64 = NewType("Base64", str)


@attr.attrs(auto_attribs=True, frozen=True)
class CroppedAnnotation:
    image: Base64
    fragment_number: MuseumNumber
    script: str
    label: str


class AnnotationImageExtractor:
    def __init__(
        self,
        fragment_repository: FragmentRepository,
        annotations_repository: AnnotationsRepository,
        photos_repository: FileRepository,
    ):
        self._fragments_repository = fragment_repository
        self._annotations_repository = annotations_repository
        self._photos_repository = photos_repository

    def cropped_images_from_sign(self, sign: str) -> Sequence[CroppedAnnotation]:
        annotations = self._annotations_repository.find_by_sign(sign)
        result = []
        for single_annotation in annotations:
            fragment_number = single_annotation.fragment_number
            for annotation in single_annotation.annotations:
                script, label = self._get_info(annotation, fragment_number)
                cropped_image = self._crop_from_annotation(annotation, fragment_number)
                cropped_image_result = CroppedAnnotation(
                    cropped_image, fragment_number, script, label
                )
                result.append(cropped_image_result)
        return result

    def _get_info(self, annotation: Annotation, fragmen_number: MuseumNumber):
        fragment = self._fragments_repository.query_by_museum_number(fragmen_number)
        script = fragment.script
        return script, "test-label"

    def _crop_from_annotation(
        self, annotation: Annotation, fragment_number: MuseumNumber
    ) -> Base64:
        fragment_image = self._photos_repository.query_by_file_name(
            f"{fragment_number}.jpg"
        )
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        bounding_boxes = BoundingBox.from_annotations(
            image.size[0], image.size[1], [annotation]
        )[0]
        area = (
            bounding_boxes.top_left_x,
            bounding_boxes.top_left_y,
            bounding_boxes.top_left_x + bounding_boxes.width,
            bounding_boxes.top_left_y + bounding_boxes.height,
        )
        cropped_image = image.crop(area)
        buf = io.BytesIO()
        cropped_image.save(buf, format="PNG")
        return Base64(base64.b64encode(buf.getvalue()).decode("utf-8"))
