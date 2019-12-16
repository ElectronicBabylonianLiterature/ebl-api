from ebl.fragmentarium.application.annotation_service import AnnotationService
from ebl.tests.factories.annotation import AnnotationsFactory


def test_find(annotations_repository, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).query_by_fragment_number(
        annotations.fragment_number
    ).thenReturn(annotations)
    service = AnnotationService(annotations_repository)

    assert service.find(annotations.fragment_number) == annotations


def test_update(annotations_repository, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).create_or_update(annotations).thenReturn()
    service = AnnotationService(annotations_repository)

    assert service.update(annotations) == annotations
