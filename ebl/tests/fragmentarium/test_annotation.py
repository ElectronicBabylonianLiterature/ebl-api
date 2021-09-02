from ebl.fragmentarium.domain.annotation import (
    Geometry,
    AnnotationData,
    Annotation,
    Annotations,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber

HEIGHT = 3.5
WIDTH = 0.32
Y = 35.4
X = 34.2
GEOMETRY = Geometry(X, Y, WIDTH, HEIGHT)

PATH = [2, 3]
VALUE = "kur"
ID = "1234"
SIGN_NAME = "KUR"
DATA = AnnotationData(ID, VALUE, PATH, SIGN_NAME)

ANNOTATION = Annotation(GEOMETRY, DATA)

MUSEUM_NUMBER = MuseumNumber("K", "1")
ANNOTATIONS = Annotations(MUSEUM_NUMBER, [ANNOTATION])


def test_geometry():
    assert GEOMETRY.x == X
    assert GEOMETRY.y == Y
    assert GEOMETRY.width == WIDTH
    assert GEOMETRY.height == HEIGHT


def test_data():
    assert DATA.id == ID
    assert DATA.value == VALUE
    assert DATA.path == PATH
    assert DATA.sign_name == SIGN_NAME


def test_annotation():
    assert ANNOTATION.geometry == GEOMETRY
    assert ANNOTATION.data == DATA


def test_annotations():
    assert ANNOTATIONS.fragment_number == MUSEUM_NUMBER
    assert ANNOTATIONS.annotations == [ANNOTATION]
