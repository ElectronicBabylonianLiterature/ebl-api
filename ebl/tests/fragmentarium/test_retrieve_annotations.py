import ebl.fragmentarium.retrieve_annotations as retrieve_annotations
from ebl.fragmentarium.retrieve_annotations import create_annotations
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    GeometryFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_create_annotations(context, when):
    annotation_repository = context.annotations_repository
    fragment_repository = context.fragment_repository
    annotation = AnnotationsFactory.build()
    fragment = TransliteratedFragmentFactory.build()

    fragment_repository.create(fragment)
    annotation_repository.create_or_update(annotation)

    when(retrieve_annotations).save_image(...).thenReturn(
        (str(fragment.number), (640, 480))
    )
    when(retrieve_annotations).write_annotations(...).thenReturn(None)

    assert create_annotations([annotation], "", "", context) is None


def test_convert_bboxes():
    geometry = GeometryFactory.build(x=0, y=0, width=100, height=100)
    annotation = AnnotationFactory.build(geometry=geometry)
    shape = (640, 480)
    assert retrieve_annotations.convert_bboxes(shape, [annotation]) == (
        (0, 0, 640, 0, 640, 480, 0, 480),
    )
