from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
    CroppedAnnotation,
)
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
)


def test_find_annotations_by_sign(annotations_repository, when):
    service = CroppedAnnotationService(annotations_repository)
    annotation = AnnotationFactory.build_batch(2)
    annotations = [AnnotationsFactory.build(annotations=annotation)]

    when(annotations_repository).find_by_sign("test-sign").thenReturn(annotations)
    assert service.find_annotations_by_sign("test-sign") == list(
        map(
            lambda x: CroppedAnnotation(
                x.cropped_sign.cropped_sign,
                x.cropped_sign.script,
                x.cropped_sign.label,
                annotations[0].fragment_number,
            ),
            annotation,
        )
    )
