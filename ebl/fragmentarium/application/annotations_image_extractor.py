import io
from io import BytesIO
from typing import Sequence

import pydash
from PIL import Image

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.domain.annotation import Annotations, BoundingBox


class AnnotationImageExtractor:
    def __init__(
        self,
        annotations: AnnotationsRepository,
        photos: FileRepository,

    ):
        self._annotations = annotations
        self._photos = photos

    def cropped_images_from_sign(self, sign: str) -> Sequence[bytes]:
        annotations = self._annotations.find_by_sign(sign)
        return pydash.flatten([self._crop_from_annotation(annotation) for annotation in annotations])

    def _crop_from_annotation(self, annotation: Annotations) -> Sequence[bytes]:
        fragment_image = self._photos.query_by_file_name(f"{annotation.fragment_number}.jpg")
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        bounding_boxes = BoundingBox.from_annotations(
            image.size[0], image.size[1], annotation.annotations
        )
        cropped_images = []
        for bbox in bounding_boxes:
            area = (bbox.top_left_x, bbox.top_left_y, bbox.width, bbox.height)
            cropped_image = image.crop(area)
            buf = io.BytesIO()
            cropped_image.save(buf, format="JPEG")
            cropped_images.append(buf.getvalue())
        return cropped_images




