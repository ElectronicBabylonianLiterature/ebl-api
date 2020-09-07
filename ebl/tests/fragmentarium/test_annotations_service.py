from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.tests.factories.annotation import AnnotationsFactory


SCHEMA = AnnotationsSchema()


def test_find(annotations_repository, changelog, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).query_by_fragment_number(
        annotations.fragment_number
    ).thenReturn(annotations)
    service = AnnotationsService(annotations_repository, changelog)

    assert service.find(annotations.fragment_number) == annotations


def test_update(annotations_repository, when, user, changelog):
    fragment_number = "K.1"
    annotations = AnnotationsFactory.build(fragment_number=fragment_number)
    updated_annotations = AnnotationsFactory.build(fragment_number=fragment_number)

    when(annotations_repository).query_by_fragment_number(fragment_number).thenReturn(
        annotations
    )
    when(annotations_repository).create_or_update(updated_annotations).thenReturn()
    when(changelog).create(
        "annotations",
        user.profile,
        {"_id": fragment_number, **SCHEMA.dump(annotations)},
        {"_id": fragment_number, **SCHEMA.dump(updated_annotations)},
    ).thenReturn()

    service = AnnotationsService(annotations_repository, changelog)

    assert service.update(updated_annotations, user) == updated_annotations
