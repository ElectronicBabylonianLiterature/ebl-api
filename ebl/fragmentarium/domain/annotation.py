from typing import Sequence, Dict
from uuid import uuid4

import attr

from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.retrieve_annotations import BoundingBox


@attr.s(auto_attribs=True, frozen=True)
class BoundingBoxPrediction(BoundingBox):
    probability: float

    @classmethod
    def from_dict(
        cls, bounding_boxes_prediction_dict: Dict
    ) -> "BoundingBoxPrediction":
        return cls(
            bounding_boxes_prediction_dict["top_left_x"],
            bounding_boxes_prediction_dict["top_left_y"],
            bounding_boxes_prediction_dict["width"],
            bounding_boxes_prediction_dict["height"],
            bounding_boxes_prediction_dict["probability"],
        )


@attr.attrs(auto_attribs=True, frozen=True)
class Geometry:
    x: float
    y: float
    width: float
    height: float


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationData:
    id: str
    value: str
    path: Sequence[int]
    sign_name: str


@attr.attrs(auto_attribs=True, frozen=True)
class Annotation:
    geometry: Geometry
    data: AnnotationData

    @classmethod
    def from_prediction(cls, geometry: Geometry) -> "Annotation":
        data = AnnotationData(uuid4().hex, "", [], "")
        return cls(geometry, data)


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
