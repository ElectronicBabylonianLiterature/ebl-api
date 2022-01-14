import pytest

from ebl.fragmentarium.application.annotations_image_extractor import (
    AnnotationImageExtractor,
    CroppedAnnotation,
)
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
def test_format_line_label(
    line_label, expected, annotations_repository, photo_repository, fragment_repository
):
    image_extractor = AnnotationImageExtractor(
        fragment_repository, annotations_repository, photo_repository
    )
    assert image_extractor._format_label(line_label) == expected


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
    fragment_repository,
    annotations_repository,
    photo_repository,
):
    image_extractor = AnnotationImageExtractor(
        fragment_repository, annotations_repository, photo_repository
    )
    assert image_extractor._is_matching_number(line_label, line_number) == expected


def test_cropped_images_from_sign(
    annotations_repository,
    photo_repository,
    fragment_repository,
    when,
    photo_jpeg,
    text_with_labels,
):

    image_extractor = AnnotationImageExtractor(
        fragment_repository, annotations_repository, photo_repository
    )

    single_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(path=[2, 0, 0])
    )
    annotation = AnnotationsFactory.build(annotations=[single_annotation])
    sign = "test-sign"

    fragment = TransliteratedFragmentFactory.build(text=text_with_labels)
    (when(annotations_repository).find_by_sign(sign).thenReturn([annotation]))
    (
        when(fragment_repository)
        .query_by_museum_number(annotation.fragment_number)
        .thenReturn(fragment)
    )
    (
        when(photo_repository)
        .query_by_file_name(f"{annotation.fragment_number}.jpg")
        .thenReturn(photo_jpeg)
    )

    result = image_extractor.cropped_images_from_sign(sign)
    assert len(result) > 0
    first_cropped_annotation = result[0]
    assert isinstance(first_cropped_annotation, CroppedAnnotation)
    assert first_cropped_annotation.script == fragment.script
    assert first_cropped_annotation.label == "i Stone wig Stone wig 2"
