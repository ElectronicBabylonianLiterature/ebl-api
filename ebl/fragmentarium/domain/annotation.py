import base64
import io
from PIL import Image
from enum import Enum
from typing import Sequence, Optional
from uuid import uuid4

import attr

from ebl.fragmentarium.application.cropped_sign_image import CroppedSign, Base64
from ebl.fragmentarium.domain.fragment import Script
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.attrs(auto_attribs=True, frozen=True)
class Geometry:
    x: float
    y: float
    width: float
    height: float


class AnnotationValueType(Enum):
    HAS_SIGN = "HasSign"
    NUMBER = "Number"
    SURFACE_AT_LINE = "SurfaceAtLine"
    RULING_DOLLAR_LINE = "RulingDollarLine"
    BLANK = "Blank"
    PREDICTED = "Predicted"
    PARTIALLY_BROKEN = "PartiallyBroken"
    DAMAGED = "Damaged"
    STRUCT = "Struct"
    UnclearSign = "UnclearSign"
    ColumnAtLine = "ColumnAtLine"
    CompoundGrapheme = "CompoundGrapheme"


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationData:
    id: str
    value: str
    type: AnnotationValueType
    path: Sequence[int]
    sign_name: str


@attr.attrs(auto_attribs=True, frozen=True)
class Annotation:
    geometry: Geometry
    data: AnnotationData
    cropped_sign: Optional[CroppedSign]

    def crop_image(self, image: Image.Image) -> Base64:
        bounding_box = BoundingBox.from_annotations(
            image.size[0], image.size[1], [self]
        )[0]
        area = (
            int(bounding_box.top_left_x),
            int(bounding_box.top_left_y),
            int(bounding_box.top_left_x + bounding_box.width),
            int(bounding_box.top_left_y + bounding_box.height),
        )
        cropped_image = image.crop(area)
        MAX_SIZE = (800, 800)
        if cropped_image.size[0] * cropped_image.size[1] >= MAX_SIZE[0] * MAX_SIZE[1]:
            cropped_image.thumbnail(MAX_SIZE)
        buf = io.BytesIO()
        cropped_image.save(buf, format="PNG")
        return Base64(base64.b64encode(buf.getvalue()).decode("utf-8"))

    @classmethod
    def from_prediction(cls, geometry: Geometry) -> "Annotation":
        data = AnnotationData(uuid4().hex, "", AnnotationValueType.PREDICTED, [], "")
        return cls(geometry, data, None)


@attr.attrs(auto_attribs=True, frozen=True)
class BoundingBox:
    top_left_x: float
    top_left_y: float
    width: float
    height: float

    def to_list(self) -> Sequence[float]:
        return [self.top_left_x, self.top_left_y, self.width, self.height]

    @classmethod
    def from_relative_coordinates(
        cls,
        relative_x,
        relative_y,
        relative_width,
        relative_height,
        image_width,
        image_height,
    ) -> "BoundingBox":
        absolute_x = int(round(relative_x / 100 * image_width))
        absolute_y = int(round(relative_y / 100 * image_height))
        absolute_width = int(round(relative_width / 100 * image_width))
        absolute_height = int(round(relative_height / 100 * image_height))
        return cls(absolute_x, absolute_y, absolute_width, absolute_height)

    @staticmethod
    def from_annotations(
        image_width: int, image_height: int, annotations: Sequence[Annotation]
    ) -> Sequence["BoundingBox"]:
        return tuple(
            BoundingBox.from_relative_coordinates(
                annotation.geometry.x,
                annotation.geometry.y,
                annotation.geometry.width,
                annotation.geometry.height,
                image_width,
                image_height,
            )
            for annotation in annotations
        )


@attr.s(auto_attribs=True, frozen=True)
class BoundingBoxPrediction(BoundingBox):
    probability: float


@attr.attrs(auto_attribs=True, frozen=True)
class Annotations:
    fragment_number: MuseumNumber
    annotations: Sequence[Annotation] = tuple()
    script: Optional[Script] = None

    @classmethod
    def from_bounding_boxes_predictions(
        cls,
        fragment_number: MuseumNumber,
        bboxes: Sequence[BoundingBoxPrediction],
        image_height: int,
        image_width: int,
    ) -> "Annotations":
        annotations = []
        for bbox in bboxes:
            geometry = Geometry(
                bbox.top_left_x / image_width * 100,
                bbox.top_left_y / image_height * 100,
                bbox.width / image_width * 100,
                bbox.height / image_width * 100,
            )
            annotations.append(Annotation.from_prediction(geometry))
        return cls(fragment_number, annotations)
