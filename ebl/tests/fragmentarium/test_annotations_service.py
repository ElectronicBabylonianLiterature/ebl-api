from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber


import pytest

from ebl.tests.conftest import create_test_photo
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    AnnotationDataFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange

SCHEMA = AnnotationsSchema()


@pytest.mark.parametrize(
    "line_label, expected",
    [
        (
            LineLabel(
                ColumnLabel.from_int(1),
                SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
                ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
                LineNumber(2),
            ),
            "i Stone wig Stone wig 2",
        ),
        (
            LineLabel(
                None, None, None, LineNumberRange(LineNumber(1, True), LineNumber(3))
            ),
            "1'-3",
        ),
    ],
)
def test_format_line_label(line_label, expected, annotations_service):
    assert annotations_service._format_label(line_label) == expected


@pytest.mark.parametrize(
    "line_label, line_number, expected",
    [
        (
            LineNumber(2),
            2,
            True,
        ),
        (
            LineNumber(2),
            1,
            False,
        ),
        (
            LineNumberRange(LineNumber(1, True), LineNumber(3)),
            2,
            True,
        ),
        (
            LineNumberRange(LineNumber(1, True), LineNumber(3)),
            4,
            False,
        ),
    ],
)
def test_line_label_match_line_number(
    line_label,
    line_number,
    expected,
    annotations_service,
):
    assert annotations_service._is_matching_number(line_label, line_number) == expected


def test_cropped_images_from_sign(
    annotations_repository,
    fragment_repository,
    photo_repository,
    when,
    text_with_labels,
    annotations_service,
):
    single_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(path=[2, 0, 0])
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
    for annotation, cropped_image in zip(annotations.annotations, cropped_images):
        assert annotation.cropped_sign.image_id == cropped_image.image_id
        assert annotation.cropped_sign.script == fragment.script
        assert annotation.cropped_sign.label == "i Stone wig Stone wig 2"


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
    expected = Annotations(fragment_number, tuple())
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
    when,
    user,
    changelog,
    text_with_labels,
):
    fragment_number = MuseumNumber("K", "1")
    annotations = AnnotationsFactory.build(fragment_number=fragment_number)
    updated_annotations = AnnotationsFactory.build(fragment_number=fragment_number)

    fragment = TransliteratedFragmentFactory.build(text=text_with_labels)
    when(annotations_repository).query_by_museum_number(fragment_number).thenReturn(
        annotations
    )
    when(annotations_repository).create_or_update(updated_annotations).thenReturn()
    when(changelog).create_many(
        "annotations",
        user.profile,
        {"_id": str(fragment_number), **SCHEMA.dump(annotations)},
        {"_id": str(fragment_number), **SCHEMA.dump(updated_annotations)},
    ).thenReturn()
    (
        when(fragment_repository)
        .query_by_museum_number(annotations.fragment_number)
        .thenReturn(fragment)
    )
    (
        when(photo_repository)
        .query_by_file_name(f"{annotations.fragment_number}.jpg")
        .thenReturn(create_test_photo("K.2"))
    )
    result = annotations_service.update(updated_annotations, user)
    assert result.fragment_number == updated_annotations.fragment_number
    for result_annotation, annotation in zip(
        result.annotations, updated_annotations.annotations
    ):
        assert result_annotation.geometry == annotation.geometry
        assert result_annotation.data == annotation.data
        assert result_annotation.cropped_sign is not None
