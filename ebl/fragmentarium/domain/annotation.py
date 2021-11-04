from enum import Enum
from typing import Sequence
from uuid import uuid4

import attr

from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.attrs(auto_attribs=True, frozen=True)
class Geometry:
    x: float
    y: float
    width: float
    height: float


class AnnotationValueType(Enum):
    HASSIGN = "HasSign"
    NUMBER = "Number"
    SURFACEATLINE = "SurfaceAtLine"
    RULINGDOLLARLINE = "RulingDollarLine"
    BLANK = "Blank"
    PREDICTED = "Predicted"
    PARTIALLY_BROKEN = "PartiallyBroken"


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

    @classmethod
    def from_prediction(cls, geometry: Geometry) -> "Annotation":
        data = AnnotationData(uuid4().hex, "", AnnotationValueType.PREDICTED, [], "")
        return cls(geometry, data)


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
        return tuple(BoundingBox.from_relative_coordinates(
                    annotation.geometry.x,
                    annotation.geometry.y,
                    annotation.geometry.width,
                    annotation.geometry.height,
                    image_width,
                    image_height,
                ) for annotation in annotations)


@attr.s(auto_attribs=True, frozen=True)
class BoundingBoxPrediction(BoundingBox):
    probability: float


@attr.attrs(auto_attribs=True, frozen=True)
class Annotations:
    fragment_number: MuseumNumber
    annotations: Sequence[Annotation] = tuple()

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
