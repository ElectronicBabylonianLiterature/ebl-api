from typing import cast

from mockito import mock, verify

from ebl.fragmentarium.application.annotations_repository import (
    AnnotationsRepository,
)
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
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
    CroppedSignFactory,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.fragment import FragmentFactory


def test_find_annotations_by_sign_passes_centroids_only_filter(
    fragment_repository: MongoFragmentRepository,
    when,
):
    annotations_repository = cast(AnnotationsRepository, mock())
    cropped_sign_images_repository = cast(CroppedSignImagesRepository, mock())

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    when(annotations_repository).find_by_sign(
        "test-sign", True, False, None, None
    ).thenReturn([])

    result = service.find_annotations_by_sign("test-sign", centroids_only=True)

    assert result == []
    verify(annotations_repository, times=1).find_by_sign(
        "test-sign", True, False, None, None
    )


def test_find_annotations_by_sign_passes_cluster_and_script_filters(
    fragment_repository: MongoFragmentRepository,
    when,
):
    annotations_repository = cast(AnnotationsRepository, mock())
    cropped_sign_images_repository = cast(CroppedSignImagesRepository, mock())

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    when(annotations_repository).find_by_sign(
        "test-sign", False, False, "test-cluster-id", "Neo-Assyrian"
    ).thenReturn([])

    result = service.find_annotations_by_sign(
        "test-sign",
        cluster_id="test-cluster-id",
        script_filter="Neo-Assyrian",
    )

    assert result == []
    verify(annotations_repository, times=1).find_by_sign(
        "test-sign", False, False, "test-cluster-id", "Neo-Assyrian"
    )


def test_find_annotations_by_sign_deduplicates_fetch_date_and_image_lookups(when):
    annotations_repository = cast(AnnotationsRepository, mock())
    cropped_sign_images_repository = cast(CroppedSignImagesRepository, mock())
    fragment_repository = cast(FragmentRepository, mock())

    service = CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    shared_image_id = "shared-image-id"
    annotation = AnnotationFactory.build_batch(
        2,
        cropped_sign=CroppedSignFactory.build(image_id=shared_image_id),
    )
    annotations = AnnotationsWithScriptFactory.build(annotations=annotation)
    fragment = FragmentFactory.build(number=annotations.fragment_number)

    when(annotations_repository).find_by_sign(
        "test-sign", False, False, None, None
    ).thenReturn([annotations])
    when(fragment_repository).fetch_date(annotations.fragment_number).thenReturn(
        fragment.date
    )
    when(cropped_sign_images_repository).query_by_id(shared_image_id).thenReturn(
        CroppedSignImage(
            shared_image_id,
            Base64("shared-base64"),
            annotations.fragment_number,
        )
    )

    result = service.find_annotations_by_sign("test-sign")

    assert len(result) == 2
    verify(fragment_repository, times=1).fetch_date(annotations.fragment_number)
    verify(cropped_sign_images_repository, times=1).query_by_id(shared_image_id)
