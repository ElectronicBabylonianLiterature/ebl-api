import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.annotations_schema import AnnotationSchema


@pytest.fixture
def base_annotation_data():
    return {
        "geometry": {"x": 1.0, "y": 2.0, "width": 3.0, "height": 4.0},
        "data": {
            "id": "abc123",
            "value": "NAM",
            "path": [1, 2],
        },
        "pcaClustering": {
            "clusterId": "cluster-1",
            "clusterRank": 0,
            "form": "canonical1",
            "isCentroid": False,
            "clusterSize": 26,
            "isMain": True,
        },
    }


def test_annotation_schema_with_pca_clustering_roundtrip(base_annotation_data):
    schema = AnnotationSchema()
    loaded = schema.load(base_annotation_data)
    dumped = schema.dump(loaded)
    assert dumped["pcaClustering"]["clusterId"] == "cluster-1"
    assert dumped["pcaClustering"]["form"] == "canonical1"
    assert dumped["pcaClustering"]["isCentroid"] is False
    assert dumped["pcaClustering"]["clusterSize"] == 26
    assert dumped["pcaClustering"]["isMain"] is True


def test_pca_clustering_omitted_when_none(base_annotation_data):
    schema = AnnotationSchema()
    data_without_pca = base_annotation_data.copy()
    data_without_pca.pop("pcaClustering")
    loaded = schema.load(data_without_pca)
    dumped = schema.dump(loaded)
    assert "pcaClustering" not in dumped


@pytest.mark.parametrize(
    "invalid_field, invalid_value",
    [
        ("clusterId", None),
        ("clusterRank", "not-an-int"),
        ("form", None),
        ("isCentroid", "not-a-bool"),
        ("clusterSize", "NaN"),
        ("isMain", "yes"),
    ],
)
def test_invalid_pca_clustering_fields_raise_validation_error(base_annotation_data, invalid_field, invalid_value):
    schema = AnnotationSchema()
    invalid_data = base_annotation_data.copy()
    invalid_data["pcaClustering"] = invalid_data["pcaClustering"].copy()
    invalid_data["pcaClustering"][invalid_field] = invalid_value
    with pytest.raises(ValidationError):
        schema.load(invalid_data)


def test_partial_pca_clustering_missing_fields_raises(base_annotation_data):
    schema = AnnotationSchema()
    partial_data = base_annotation_data.copy()
    partial_data["pcaClustering"] = {"clusterId": "cluster-1"}
    with pytest.raises(ValidationError):
        schema.load(partial_data)


def test_pca_clustering_variants(base_annotation_data):
    schema = AnnotationSchema()
    variant_data = base_annotation_data.copy()
    variant_data["pcaClustering"]["form"] = "variant1"
    loaded = schema.load(variant_data)
    dumped = schema.dump(loaded)
    assert dumped["pcaClustering"]["form"] == "variant1"


def test_pca_clustering_is_centroid_true(base_annotation_data):
    schema = AnnotationSchema()
    data = base_annotation_data.copy()
    data["pcaClustering"]["isCentroid"] = True
    loaded = schema.load(data)
    dumped = schema.dump(loaded)
    assert dumped["pcaClustering"]["isCentroid"] is True