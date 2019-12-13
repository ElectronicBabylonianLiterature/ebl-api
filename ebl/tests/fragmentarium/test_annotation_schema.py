from ebl.fragmentarium.application.annotation_schema import AnnotationSchema
from ebl.fragmentarium.domain.annotation import Annotation, Geometry, AnnotationData

HEIGHT = 34.5
WIDTH = 100.0
Y = 34
X = 0.04

PATH = [3, 4, 6]
VALUE = "kur"
ID = "abc123"

ANNOTATION = Annotation(Geometry(X, Y, WIDTH, HEIGHT), AnnotationData(ID, VALUE, PATH))

SERIALIZED = {
    "geometry": {"x": X, "y": Y, "width": WIDTH, "height": HEIGHT},
    "data": {"id": ID, "value": VALUE, "path": PATH},
}


def test_load():
    assert AnnotationSchema().load(SERIALIZED) == ANNOTATION


def test_dump():
    assert AnnotationSchema().dump(ANNOTATION) == SERIALIZED
