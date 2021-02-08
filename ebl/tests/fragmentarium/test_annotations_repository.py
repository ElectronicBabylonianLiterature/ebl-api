from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.annotation import AnnotationsFactory

COLLECTION = "annotations"


def test_create(database, annotations_repository):
    annotations = AnnotationsFactory.build()
    fragment_number = annotations.fragment_number

    annotations_repository.create_or_update(annotations)

    assert database[COLLECTION].find_one(
        {"fragmentNumber": str(fragment_number)}, {"_id": False}
    ) == AnnotationsSchema().dump(annotations)


def test_update(database, annotations_repository):
    annotations = AnnotationsFactory.build()
    fragment_number = annotations.fragment_number
    updated = AnnotationsFactory.build(fragment_number=fragment_number)

    annotations_repository.create_or_update(annotations)
    annotations_repository.create_or_update(updated)

    assert database[COLLECTION].find_one(
        {"fragmentNumber": str(fragment_number)}, {"_id": False}
    ) == AnnotationsSchema().dump(updated)


def test_query_by_museum_number(database, annotations_repository):
    annotations = AnnotationsFactory.build()
    fragment_number = annotations.fragment_number

    database[COLLECTION].insert_one(AnnotationsSchema().dump(annotations))

    assert annotations_repository.query_by_museum_number(fragment_number) == annotations


def test_query_by_museum_number_not_found(database, annotations_repository):
    fragment_number = MuseumNumber("X", "1")

    assert annotations_repository.query_by_museum_number(
        fragment_number
    ) == Annotations(fragment_number)
