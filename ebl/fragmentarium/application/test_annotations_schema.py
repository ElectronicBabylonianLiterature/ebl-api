import pytest
from marshmallow import ValidationError
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import PcaClustering, Annotation, AnnotationData


def sample_annotation_with_pca():
    return {
        "annotationId": "1234",
        "pcaClustering": {
            "clusterId": "abcd-1234",
            "clusterRank": 0,
            "form": "canonical1",
            "isCentroid": True,
            "clusterSize": 10,
        },
    }


def sample_annotation_without_pca():
    return {"annotationId": "1234", "pcaClustering": None}


@pytest.fixture
def schema():
    return AnnotationsSchema()


def test_save_load_cycle_with_pca(schema):
    annotation = sample_annotation_with_pca()
    dumped = schema.dump(annotation)
    loaded = schema.load(dumped)
    assert loaded["pcaClustering"] == annotation["pcaClustering"]


def test_omit_pca_when_none(schema):
    annotation = sample_annotation_without_pca()
    dumped = schema.dump(annotation)
    loaded = schema.load(dumped)
    assert loaded.get("pcaClustering") is None


@pytest.mark.parametrize(
    "malformed_payload",
    [
        {"clusterId": "abcd-1234"},
        {"clusterRank": 0},
        {"clusterId": "id", "clusterRank": 1, "form": "x"},
    ],
)
def test_malformed_pcaClustering(schema, malformed_payload):
    annotation = {"annotationId": "1234", "pcaClustering": malformed_payload}
    with pytest.raises(ValidationError):
        schema.load(annotation)


def test_complete_pca_required(schema):
    annotation = sample_annotation_with_pca()
    loaded = schema.load(annotation)
    assert loaded["pcaClustering"]["clusterId"] == "abcd-1234"
    incomplete = annotation.copy()
    incomplete["pcaClustering"] = {
        k: v
        for k, v in annotation["pcaClustering"].items()
        if k != "clusterSize"
    }
    with pytest.raises(ValidationError):
        schema.load(incomplete)