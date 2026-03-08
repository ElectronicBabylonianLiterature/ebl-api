from ebl.fragmentarium.application.annotations_schema import (
    AnnotationsWithScriptSchema,
    AnnotationsSchema,
)
from ebl.fragmentarium.application.cropped_sign_image import CroppedSign
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    Geometry,
    AnnotationData,
    Annotations,
    AnnotationValueType,
)
from ebl.tests.factories.fragment import ScriptFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
import pytest
from marshmallow import ValidationError


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
PROVENANCE = "ASSUR"
SCRIPT = ScriptFactory.build()
SCRIPT_DUMPED = ScriptSchema().dump(SCRIPT)
LABEL = "label"
ANNOTATION = Annotation(
    Geometry(X, Y, WIDTH, HEIGHT),
    AnnotationData(ID, VALUE, TYPE, PATH, SIGN_NAME),
    CroppedSign(IMAGE_ID, LABEL),
)

MUSEUM_NUMBER = MuseumNumber("K", "1")
ANNOTATIONS = Annotations(MUSEUM_NUMBER, [ANNOTATION], SCRIPT, PROVENANCE)


SERIALIZED = {
    "fragmentNumber": str(MUSEUM_NUMBER),
    "script": SCRIPT_DUMPED,
    "provenance": PROVENANCE,
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
                "label": LABEL,
            },
        }
    ],
}


def test_load():
    assert AnnotationsWithScriptSchema().load(SERIALIZED) == ANNOTATIONS


def test_dump():
    assert AnnotationsWithScriptSchema().dump(ANNOTATIONS) == SERIALIZED


def sample_annotation_with_pca():
    return {
        "fragmentNumber": "K.123",
        "annotations": [
            {
                "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
                "data": {"id": "d1", "value": "X", "path": [1, 2, 3]},
                "pcaClustering": {
                    "clusterId": "abcd-1234",
                    "clusterRank": 0,
                    "form": "canonical1",
                    "isCentroid": True,
                    "clusterSize": 10,
                    "isMain": True,
                },
            }
        ],
    }


def sample_annotation_without_pca():
    return {
        "fragmentNumber": "K.123",
        "annotations": [
            {
                "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
                "data": {"id": "d1", "value": "X", "path": [1, 2, 3]},
                "pcaClustering": None,
            }
        ],
    }


@pytest.fixture
def schema():
    return AnnotationsSchema()


def test_save_load_cycle_with_pca(schema):
    annotation = sample_annotation_with_pca()
    loaded = schema.load(annotation)
    pca = loaded.annotations[0].pca_clustering
    expected = annotation["annotations"][0]["pcaClustering"]

    assert pca.cluster_id == expected["clusterId"]
    assert pca.cluster_rank == expected["clusterRank"]
    assert pca.form == expected["form"]
    assert pca.is_centroid == expected["isCentroid"]
    assert pca.cluster_size == expected["clusterSize"]
    assert pca.is_main == expected["isMain"]


def test_omit_pca_when_none(schema):
    annotation = sample_annotation_without_pca()
    loaded = schema.load(annotation)
    assert loaded.annotations[0].pca_clustering is None


@pytest.mark.parametrize(
    "malformed_payload",
    [
        {"clusterId": "abcd-1234"},
        {"clusterRank": 0},
        {"clusterId": "id", "clusterRank": 1, "form": "x"},
    ],
)
def test_malformed_pcaClustering(schema, malformed_payload):
    annotation = sample_annotation_with_pca()
    annotation["annotations"][0]["pcaClustering"] = malformed_payload
    with pytest.raises(ValidationError):
        schema.load(annotation)


def test_complete_pca_required(schema):
    annotation = sample_annotation_with_pca()
    loaded = schema.load(annotation)
    assert loaded.annotations[0].pca_clustering.cluster_id == "abcd-1234"

    incomplete = sample_annotation_with_pca()
    del incomplete["annotations"][0]["pcaClustering"]["clusterSize"]
    with pytest.raises(ValidationError):
        schema.load(incomplete)
