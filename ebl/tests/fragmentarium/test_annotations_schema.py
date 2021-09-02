from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    Geometry,
    AnnotationData,
    Annotations,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber

HEIGHT = 34.5
WIDTH = 100.0
Y = 34
X = 0.04

PATH = [3, 4, 6]
VALUE = "kur"
ID = "abc123"

ANNOTATION = Annotation(Geometry(X, Y, WIDTH, HEIGHT), AnnotationData(ID, VALUE, PATH))

MUSEUM_NUMBER = MuseumNumber("K", "1")
ANNOTATIONS = Annotations(MUSEUM_NUMBER, [ANNOTATION])

SERIALIZED = {
    "fragmentNumber": str(MUSEUM_NUMBER),
    "annotations": [
        {
            "geometry": {"x": X, "y": Y, "width": WIDTH, "height": HEIGHT},
            "data": {"id": ID, "value": VALUE, "path": PATH},
        }
    ],
}


def test_load():
    assert AnnotationsSchema().load(SERIALIZED) == ANNOTATIONS


def test_dump():
    assert AnnotationsSchema().dump(ANNOTATIONS) == SERIALIZED
