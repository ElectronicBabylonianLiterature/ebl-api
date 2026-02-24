import attr
from itertools import zip_longest

from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.cropped_sign_image import Base64, CroppedSignImage
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.tests.conftest import create_test_photo
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    AnnotationDataFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

SCHEMA = AnnotationsSchema()


def test_cropped_images_from_sign(
    annotations_repository,
    fragment_repository,
    photo_repository,
    when,
    text_with_labels,
    annotations_service,
):
    single_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(path=[3, 0, 0])
    )
    annotation = AnnotationsFactory.build(annotations=[single_annotation])

    fragment = TransliteratedFragmentFactory.build(text=text_with_labels)
    (
        when(fragment_repository)
        .query_by_museum_number(annotation.fragment_number)
        .thenReturn(fragment)
    )
    (
        when(photo_repository)
        .query_by_file_name(f"{annotation.fragment_number}.jpg")
        .thenReturn(create_test_photo("K.2"))
    )

    annotations, cropped_images = annotations_service._cropped_image_from_annotations(
        annotation
    )
    for annotation, cropped_image in zip_longest(
        annotations.annotations,
        cropped_images,
    ):
        assert annotation is not None
        assert cropped_image is not None
        assert annotation.cropped_sign.image_id == cropped_image.image_id
        assert annotation.cropped_sign.label == "i Stone wig"


def test_generate_annotations(
    annotations_repository,
    photo_repository,
    changelog,
    when,
    fragment_repository,
    cropped_sign_images_repository,
):
    fragment_number = MuseumNumber.of("X.0")

    image_file = create_test_photo("K.2")

    when(photo_repository).query_by_file_name(f"{fragment_number}.jpg").thenReturn(
        image_file
    )
    ebl_ai_client = EblAiClient("mock-localhost:8001")
    service = AnnotationsService(
        ebl_ai_client,
        annotations_repository,
        photo_repository,
        changelog,
        fragment_repository,
        photo_repository,
        cropped_sign_images_repository,
    )
    expected = Annotations(fragment_number, ())
    when(ebl_ai_client).generate_annotations(fragment_number, image_file, 0).thenReturn(
        expected
    )

    annotations = service.generate_annotations(fragment_number, 0)
    assert isinstance(annotations, Annotations)
    assert annotations == expected


def test_find(annotations_repository, annotations_service, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).query_by_museum_number(
        annotations.fragment_number
    ).thenReturn(annotations)

    assert annotations_service.find(annotations.fragment_number) == annotations


def test_update(
    annotations_service,
    annotations_repository,
    photo_repository,
    fragment_repository,
    cropped_sign_images_repository,
    when,
    user,
    changelog,
    text_with_labels,
):
    fragment_number = MuseumNumber("K", "1")
    fragment = TransliteratedFragmentFactory(
        number=fragment_number, text=text_with_labels
    )

    old_annotations = AnnotationsFactory.build(fragment_number=fragment_number)

    data = AnnotationDataFactory.build(path=[2, 0, 0])
    annotation = AnnotationFactory.build(cropped_sign=None, data=data)
    annotations = AnnotationsFactory.build(
        fragment_number=fragment_number, annotations=[annotation]
    )

    when(annotations_repository).query_by_museum_number(fragment_number).thenReturn(
        old_annotations
    )
    image = create_test_photo("K.2")
    when(fragment_repository).query_by_museum_number(fragment_number).thenReturn(
        fragment
    )
    (
        when(photo_repository)
        .query_by_file_name(f"{annotations.fragment_number}.jpg")
        .thenReturn(image)
    )

    expected_cropped_sign_image = CroppedSignImage(
        "test-id", Base64("test-image"), fragment_number
    )
    annotation_cropped_sign = attr.evolve(
        annotation,
        cropped_sign=CroppedSignFactory.build(
            image_id="test-id",
            label="i",
        ),
    )
    expected_annotations = attr.evolve(
        annotations, annotations=[annotation_cropped_sign]
    )
    when(CroppedSignImage).create(...).thenReturn(expected_cropped_sign_image)

    when(cropped_sign_images_repository).delete_by_fragment_number(
        fragment_number
    ).thenReturn()
    when(annotations_repository).create_or_update(expected_annotations).thenReturn()
    when(cropped_sign_images_repository).create_many(
        [expected_cropped_sign_image]
    ).thenReturn()
    schema = AnnotationsSchema()
    when(changelog).create(
        "annotations",
        user.profile,
        {"_id": str(fragment_number), **schema.dump(old_annotations)},
        {"_id": str(fragment_number), **schema.dump(expected_annotations)},
    ).thenReturn()

    result = annotations_service.update(annotations, user)
    assert result == expected_annotations
