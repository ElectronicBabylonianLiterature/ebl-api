from typing import Sequence

import attr

from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.attrs(auto_attribs=True, frozen=True)
class Geometry:
    x: float
    y: float
    width: float
    height: float


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationData:
    id: str
    sign_name: str
    value: str
    path: Sequence[int]


@attr.attrs(auto_attribs=True, frozen=True)
class Annotation:
    geometry: Geometry
    data: AnnotationData

    @staticmethod
    def from_prediction(geometry: Geometry):
        data = AnnotationData(f"generated-{uuid4}", "", "", [-1])
        return Annotation(geometry, data)


@attr.attrs(auto_attribs=True, frozen=True)
class Annotations:
    fragment_number: MuseumNumber
    annotations: Sequence[Annotation] = tuple()
