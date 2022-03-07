from ebl.fragmentarium.application.annotations_image_extractor import (
    AnnotationCroppedImageService,
    CroppedAnnotation,
)
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactoryWithImage,
)


def test_find_annotations_by_sign(annotations_repository, when):
    service = AnnotationCroppedImageService(annotations_repository)
    annotation = AnnotationFactoryWithImage.build_batch(2)
    annotations = [AnnotationsFactory.build(annotations=annotation)]

    when(annotations_repository).find_by_sign("test-sign").thenReturn(annotations)
    assert service.find_annotations_by_sign("test-sign") == list(
        map(
            lambda x: CroppedAnnotation(
                x.image.image,
                x.image.script,
                x.image.label,
                annotations[0].fragment_number,
            ),
            annotation,
        )
    )
