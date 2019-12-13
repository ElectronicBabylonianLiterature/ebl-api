from ebl.fragmentarium.domain.annotation import Geometry, AnnotationData, Annotation


HEIGHT = 3.5
WIDTH = 0.32
Y = 35.4
X = 34.2
GEOMETRY = Geometry(X, Y, WIDTH, HEIGHT)

PATH = [2, 3]
VALUE = "kur"
ID = "1234"
DATA = AnnotationData(ID, VALUE, PATH)

ANNOTATION = Annotation(GEOMETRY, DATA)


def test_geometry():
    assert GEOMETRY.x == X
    assert GEOMETRY.y == Y
    assert GEOMETRY.width == WIDTH
    assert GEOMETRY.height == HEIGHT


def test_data():
    assert DATA.id == ID
    assert DATA.value == VALUE
    assert DATA.path == PATH


def test_annotation():
    assert ANNOTATION.geometry == GEOMETRY
    assert ANNOTATION.data == DATA
