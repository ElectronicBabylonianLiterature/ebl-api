from typing import cast

from mockito import mock

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.annotation import (
    AnnotationFactory,
    AnnotationsWithScriptFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import FragmentFactory


def _service(
    annotations_repository, cropped_sign_images_repository, fragment_repository
):
    return CroppedAnnotationService(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )


def test_annotations_without_a_cropped_sign_are_skipped(
    fragment_repository: MongoFragmentRepository, when
):
    annotations_repository = cast(AnnotationsRepository, mock())
    cropped_sign_images_repository = cast(CroppedSignImagesRepository, mock())
    annotations = AnnotationsWithScriptFactory.build(
        annotations=[AnnotationFactory.build(cropped_sign=None)]
    )
    fragment = FragmentFactory.build(number=annotations.fragment_number)

    when(annotations_repository).find_by_sign(
        "test-sign", False, False, None, None, ()
    ).thenReturn([annotations])
    when(fragment_repository).fetch_date(annotations.fragment_number).thenReturn(
        fragment.date
    )

    service = _service(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    assert service.find_annotations_by_sign("test-sign") == []


def test_annotations_with_a_missing_image_are_skipped(
    fragment_repository: MongoFragmentRepository, when
):
    annotations_repository = cast(AnnotationsRepository, mock())
    cropped_sign_images_repository = cast(CroppedSignImagesRepository, mock())
    cropped_sign = CroppedSignFactory.build(image_id="missing-image-id")
    annotations = AnnotationsWithScriptFactory.build(
        annotations=[AnnotationFactory.build(cropped_sign=cropped_sign)]
    )
    fragment = FragmentFactory.build(number=annotations.fragment_number)

    when(annotations_repository).find_by_sign(
        "test-sign", False, False, None, None, ()
    ).thenReturn([annotations])
    when(fragment_repository).fetch_date(annotations.fragment_number).thenReturn(
        fragment.date
    )
    when(cropped_sign_images_repository).query_by_id("missing-image-id").thenRaise(
        NotFoundError("missing")
    )

    service = _service(
        annotations_repository, cropped_sign_images_repository, fragment_repository
    )

    assert service.find_annotations_by_sign("test-sign") == []
