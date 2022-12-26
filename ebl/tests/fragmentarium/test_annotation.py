from ebl.fragmentarium.application.cropped_sign_image import CroppedSign
from ebl.fragmentarium.domain.annotation import (
    Geometry,
    AnnotationData,
    Annotation,
    Annotations,
    BoundingBoxPrediction,
    AnnotationValueType,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.transliteration.domain.museum_number import MuseumNumber

HEIGHT = 3.5
WIDTH = 0.32
Y = 35.4
X = 34.2
GEOMETRY = Geometry(X, Y, WIDTH, HEIGHT)

PATH = [2, 3]
VALUE = "kur"
TYPE = AnnotationValueType.HAS_SIGN
ID = "1234"
SIGN_NAME = "KUR"
DATA = AnnotationData(ID, VALUE, TYPE, PATH, SIGN_NAME)

IMAGE_ID = "image-id"
SCRIPT = Script()
LABEL = "label"

CROPPED_SIGN = CroppedSign(IMAGE_ID, LABEL)

ANNOTATION = Annotation(GEOMETRY, DATA, CROPPED_SIGN)

MUSEUM_NUMBER = MuseumNumber("K", "1")
ANNOTATIONS = Annotations(MUSEUM_NUMBER, [ANNOTATION], SCRIPT)


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


def test_annotations_from_bounding_box_predictions():
    bbox_1 = BoundingBoxPrediction(0, 0, 10, 100, 0.99)
    bbox_2 = BoundingBoxPrediction(500, 500, 100, 10, 0.99)
    annotations = Annotations.from_bounding_boxes_predictions(
        MUSEUM_NUMBER, [bbox_1, bbox_2], 1000, 1000
    )
    assert annotations.annotations[0].geometry == Geometry(0.0, 0.0, 1.0, 10.0)
    assert annotations.annotations[1].geometry == Geometry(50.0, 50.0, 10.0, 1.0)


BBOX = BoundingBoxPrediction(1, 2, 3, 4, 0.99)


def test_bounding_boxes_prediction():
    assert BBOX.top_left_x == 1
    assert BBOX.top_left_y == 2
    assert BBOX.width == 3
    assert BBOX.height == 4
    assert BBOX.probability == 0.99
