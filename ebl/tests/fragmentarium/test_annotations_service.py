from itertools import zip_longest
from typing import Any, Callable, Mapping, cast

import attr
import pytest

from ebl.changelog import Changelog
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.infrastructure.cropped_sign_images_repository import (
    MongoCroppedSignImagesRepository,
)
from ebl.tests.fixtures.fixture_resolution import resolve_fixtures

from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.cropped_sign_image import Base64, CroppedSignImage
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.tests.fixtures.file_fixtures import create_test_photo
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    AnnotationDataFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

SCHEMA = AnnotationsSchema()


ANNOTATION_DEPENDENCY_FIXTURES: Mapping[str, str] = {
    name: name
    for name in (
        "annotations_repository",
        "photo_repository",
        "fragment_repository",
        "cropped_sign_images_repository",
        "changelog",
    )
}


@attr.s(frozen=True, auto_attribs=True)
class AnnotationDependencies:
    annotations_repository: AnnotationsRepository
    photo_repository: FileRepository
    fragment_repository: FragmentRepository
    cropped_sign_images_repository: MongoCroppedSignImagesRepository
    changelog: Changelog
    when: Callable[..., Any]


@pytest.fixture
def dependencies(
    request: pytest.FixtureRequest, when: Callable[..., Any]
) -> AnnotationDependencies:
    return AnnotationDependencies(
        when=when, **resolve_fixtures(request, ANNOTATION_DEPENDENCY_FIXTURES)
    )


def test_cropped_images_from_sign(
    dependencies: AnnotationDependencies, text_with_labels, annotations_service
) -> None:
    single_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(path=[3, 0, 0])
    )
    annotation = AnnotationsFactory.build(annotations=[single_annotation])

    fragment = TransliteratedFragmentFactory.build(text=text_with_labels)
    (
        dependencies.when(dependencies.fragment_repository)
        .query_by_museum_number(annotation.fragment_number)
        .thenReturn(fragment)
    )
    (
        dependencies.when(dependencies.photo_repository)
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


def test_generate_annotations(dependencies: AnnotationDependencies) -> None:
    fragment_number = MuseumNumber.of("X.0")

    image_file = create_test_photo("K.2")

    dependencies.when(dependencies.photo_repository).query_by_file_name(
        f"{fragment_number}.jpg"
    ).thenReturn(image_file)
    ebl_ai_client = EblAiClient("mock-localhost:8001")
    service = AnnotationsService(
        ebl_ai_client,
        dependencies.annotations_repository,
        dependencies.photo_repository,
        dependencies.changelog,
        dependencies.fragment_repository,
        dependencies.photo_repository,
        dependencies.cropped_sign_images_repository,
    )
    expected = Annotations(fragment_number, ())
    dependencies.when(ebl_ai_client).generate_annotations(
        fragment_number, image_file, 0
    ).thenReturn(expected)

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
    dependencies: AnnotationDependencies, annotations_service, user, text_with_labels
) -> None:
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

    dependencies.when(dependencies.annotations_repository).query_by_museum_number(
        fragment_number
    ).thenReturn(old_annotations)
    image = create_test_photo("K.2")
    dependencies.when(dependencies.fragment_repository).query_by_museum_number(
        fragment_number
    ).thenReturn(fragment)
    (
        dependencies.when(dependencies.photo_repository)
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
    dependencies.when(CroppedSignImage).create(...).thenReturn(
        expected_cropped_sign_image
    )

    dependencies.when(
        dependencies.cropped_sign_images_repository
    ).delete_by_fragment_number(fragment_number).thenReturn()
    dependencies.when(dependencies.annotations_repository).create_or_update(
        expected_annotations
    ).thenReturn()
    dependencies.when(dependencies.cropped_sign_images_repository).create_many(
        [expected_cropped_sign_image]
    ).thenReturn()
    schema = AnnotationsSchema()
    dependencies.when(dependencies.changelog).create(
        "annotations",
        user.profile,
        {"_id": str(fragment_number), **cast(dict, schema.dump(old_annotations))},
        {"_id": str(fragment_number), **cast(dict, schema.dump(expected_annotations))},
    ).thenReturn()

    result = annotations_service.update(annotations, user)
    assert result == expected_annotations
