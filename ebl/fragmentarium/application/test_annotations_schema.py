import pytest
from marshmallow import ValidationError
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema


def sample_annotation_with_pca():
    return {
        "fragmentNumber": "A123",
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
        "fragmentNumber": "A123",
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
    dumped = schema.dump(annotation)
    loaded = schema.load(dumped)
    assert (
        loaded["annotations"][0]["pcaClustering"]
        == annotation["annotations"][0]["pcaClustering"]
    )


def test_omit_pca_when_none(schema):
    annotation = sample_annotation_without_pca()
    dumped = schema.dump(annotation)
    loaded = schema.load(dumped)
    assert loaded["annotations"][0].get("pcaClustering") is None


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
    assert loaded["annotations"][0]["pcaClustering"]["clusterId"] == "abcd-1234"

    incomplete = sample_annotation_with_pca()
    del incomplete["annotations"][0]["pcaClustering"]["clusterSize"]
    with pytest.raises(ValidationError):
        schema.load(incomplete)
