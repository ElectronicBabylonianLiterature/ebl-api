from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.cropped_sign_image import CroppedSign
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    Geometry,
    AnnotationData,
    Annotations,
    AnnotationValueType,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber

HEIGHT = 34.5
WIDTH = 100.0
Y = 34
X = 0.04

PATH = [3, 4, 6]
VALUE = "kur"
TYPE = AnnotationValueType.HAS_SIGN
ID = "abc123"
SIGN_NAME = "KUR"
IMAGE_ID = "image-id"
SCRIPT = "script"
LABEL = "label"
ANNOTATION = Annotation(
    Geometry(X, Y, WIDTH, HEIGHT),
    AnnotationData(ID, VALUE, TYPE, PATH, SIGN_NAME),
    CroppedSign(IMAGE_ID, SCRIPT, LABEL),
)
ANNOTATION_NO_CROPPED_SIGN = Annotation(
    Geometry(X, Y, WIDTH, HEIGHT),
    AnnotationData(ID, VALUE, TYPE, PATH, SIGN_NAME),
    None,
)

MUSEUM_NUMBER = MuseumNumber("K", "1")
ANNOTATIONS = Annotations(MUSEUM_NUMBER, [ANNOTATION])
ANNOTATIONS_NO_CROPPED_SIGN = Annotations(MUSEUM_NUMBER, [ANNOTATION_NO_CROPPED_SIGN])

SERIALIZED = {
    "fragmentNumber": str(MUSEUM_NUMBER),
    "annotations": [
        {
            "geometry": {"x": X, "y": Y, "width": WIDTH, "height": HEIGHT},
            "data": {
                "id": ID,
                "value": VALUE,
                "type": "HasSign",
                "signName": SIGN_NAME,
                "path": PATH,
            },
            "croppedSign": {"imageId": IMAGE_ID, "script": SCRIPT, "label": LABEL},
        }
    ],
}

SERIALIZED_NO_SIGN = {
    "fragmentNumber": str(MUSEUM_NUMBER),
    "annotations": [
        {
            "geometry": {"x": X, "y": Y, "width": WIDTH, "height": HEIGHT},
            "data": {
                "id": ID,
                "value": VALUE,
                "type": "HasSign",
                "signName": SIGN_NAME,
                "path": PATH,
            },
        }
    ],
}



def test_load():
    assert AnnotationsSchema().load(SERIALIZED) == ANNOTATIONS
    x = AnnotationsSchema().load(SERIALIZED_NO_SIGN)
    assert AnnotationsSchema().load(SERIALIZED_NO_SIGN) == ANNOTATIONS_NO_CROPPED_SIGN

def test_dump():
    assert AnnotationsSchema().dump(ANNOTATIONS) == SERIALIZED
    #assert AnnotationsSchema().dump(ANNOTATIONS_NO_CROPPED_SIGN) == SERIALIZED_NO_SIGN
