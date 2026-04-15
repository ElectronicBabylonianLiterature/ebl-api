from unittest.mock import Mock
from ebl.fragmentarium.domain.annotation import PcaClustering

from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.fragmentarium.application.cropped_sign_image import (
    Base64,
    CroppedSignImage,
)
from ebl.tests.factories.annotation import (
    AnnotationFactory,
    AnnotationsWithScriptFactory,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.fragmentarium.domain.date import DateSchema


def test_find_annotations_by_sign(
    fragment_repository: MongoFragmentRepository,
):
    annotations_repository = Mock()
    cropped_sign_images_repository = Mock()

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )
    annotation = AnnotationFactory.build_batch(2)
    annotations = AnnotationsWithScriptFactory.build(annotations=annotation)

    fragment = FragmentFactory.build(number=annotations.fragment_number)
    fragment_repository.create(fragment)

    image_id_1 = annotation[0].cropped_sign.image_id
    image_id_2 = annotation[1].cropped_sign.image_id

    annotations_repository.find_by_sign.return_value = [annotations]

    cropped_sign_images_repository.query_by_id.side_effect = lambda image_id: {
        image_id_1: CroppedSignImage(
            image_id_1, Base64("test-base64-1"), annotations.fragment_number
        ),
        image_id_2: CroppedSignImage(
            image_id_2, Base64("test-base64-2"), annotations.fragment_number
        ),
    }[image_id]

    fragment_number = annotations.fragment_number
    provenance = annotations.provenance

    expected_1 = {
        "fragmentNumber": str(fragment_number),
        "image": Base64("test-base64-1"),
        "script": str(annotations.script),
        "label": annotation[0].cropped_sign.label,
        "date": DateSchema().dump(fragment.date),
        "provenance": provenance,
        "annotationId": annotation[0].data.id,
    }
    expected_2 = {
        "fragmentNumber": str(fragment_number),
        "image": Base64("test-base64-2"),
        "script": str(annotations.script),
        "label": annotation[1].cropped_sign.label,
        "date": DateSchema().dump(fragment.date),
        "provenance": provenance,
        "annotationId": annotation[1].data.id,
    }

    assert service.find_annotations_by_sign("test-sign") == [expected_1, expected_2]
    annotations_repository.find_by_sign.assert_called_once_with(
        "test-sign", False, None, None
    )

def test_find_annotations_by_sign_includes_pca_clustering(
    fragment_repository: MongoFragmentRepository,
):
    annotations_repository = Mock()
    cropped_sign_images_repository = Mock()

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    annotation = AnnotationFactory.build(
        pca_clustering=PcaClustering(
            cluster_id="test-cluster-id",
            cluster_rank=0,
            form="canonical1",
            is_centroid=True,
            cluster_size=10,
            is_main=True,
        )
    )
    annotations = AnnotationsWithScriptFactory.build(annotations=[annotation])

    fragment = FragmentFactory.build(number=annotations.fragment_number)
    fragment_repository.create(fragment)

    image_id = annotation.cropped_sign.image_id
    cropped_sign_images_repository.query_by_id.return_value = CroppedSignImage(
        image_id, Base64("test-base64"), annotations.fragment_number
    )

    annotations_repository.find_by_sign.return_value = [annotations]

    result = service.find_annotations_by_sign("test-sign")

    assert len(result) == 1
    assert result[0]["annotationId"] == annotation.data.id
    assert "pcaClustering" in result[0]

def test_find_annotations_by_sign_omits_pca_clustering_when_missing(
    fragment_repository: MongoFragmentRepository,
):
    annotations_repository = Mock()
    cropped_sign_images_repository = Mock()

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    annotation = AnnotationFactory.build(pca_clustering=None)
    annotations = AnnotationsWithScriptFactory.build(annotations=[annotation])

    fragment = FragmentFactory.build(number=annotations.fragment_number)
    fragment_repository.create(fragment)

    image_id = annotation.cropped_sign.image_id
    cropped_sign_images_repository.query_by_id.return_value = CroppedSignImage(
        image_id, Base64("test-base64"), annotations.fragment_number
    )

    annotations_repository.find_by_sign.return_value = [annotations]

    result = service.find_annotations_by_sign("test-sign")

    assert len(result) == 1
    assert result[0]["annotationId"] == annotation.data.id
    assert "pcaClustering" not in result[0]

def test_find_annotations_by_sign_passes_centroids_only_filter(
    fragment_repository: MongoFragmentRepository,
):
    annotations_repository = Mock()
    cropped_sign_images_repository = Mock()

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    annotations_repository.find_by_sign.return_value = []

    result = service.find_annotations_by_sign("test-sign", centroids_only=True)

    assert result == []
    annotations_repository.find_by_sign.assert_called_once_with(
        "test-sign", True, None, None
    )

def test_find_annotations_by_sign_passes_cluster_and_script_filters(
    fragment_repository: MongoFragmentRepository,
):
    annotations_repository = Mock()
    cropped_sign_images_repository = Mock()

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    annotations_repository.find_by_sign.return_value = []

    result = service.find_annotations_by_sign(
        "test-sign",
        cluster_id="test-cluster-id",
        script_filter="Neo-Assyrian",
    )

    assert result == []
    annotations_repository.find_by_sign.assert_called_once_with(
        "test-sign", False, "test-cluster-id", "Neo-Assyrian"
    )
