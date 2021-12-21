from ebl.fragmentarium.application.annotations_image_extractor import (
    AnnotationImageExtractor,
    CroppedAnnotation,
)
from ebl.tests.factories.annotation import AnnotationsFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_cropped_images_from_sign(
    annotations_repository, photo_repository, fragment_repository, when, photo_jpeg
):
    image_extractor = AnnotationImageExtractor(
        fragment_repository, annotations_repository, photo_repository
    )

    annotation = AnnotationsFactory.build()
    sign = "test-sign"

    fragment = TransliteratedFragmentFactory.build()
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
    assert result[0].script == fragment.script
    assert isinstance(result[0], CroppedAnnotation)
