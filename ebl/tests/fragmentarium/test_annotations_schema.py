from ebl.fragmentarium.application.cropped_sign_image import CroppedSign
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    Geometry,
    AnnotationData,
    Annotations,
    AnnotationValueType,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

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
SCRIPT = ScriptFactory.build()
SCRIPT_DUMPED = ScriptSchema().dump(SCRIPT)
LABEL = "label"
ANNOTATION = Annotation(
    Geometry(X, Y, WIDTH, HEIGHT),
    AnnotationData(ID, VALUE, TYPE, PATH, SIGN_NAME),
    CroppedSign(IMAGE_ID, LABEL),
)

MUSEUM_NUMBER = MuseumNumber("K", "1")
ANNOTATIONS = Annotations(MUSEUM_NUMBER, [ANNOTATION], SCRIPT)


SERIALIZED = {
    "fragmentNumber": str(MUSEUM_NUMBER),
    "script": SCRIPT_DUMPED,
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
            "croppedSign": {
                "imageId": IMAGE_ID,
                "script": SCRIPT_DUMPED,
                "label": LABEL,
            },
        }
    ],
}


def test_load():
    assert AnnotationsWithScriptSchema().load(SERIALIZED) == ANNOTATIONS


def test_dump():
    assert AnnotationsWithScriptSchema().dump(ANNOTATIONS) == SERIALIZED
