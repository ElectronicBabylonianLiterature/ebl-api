from ebl.fragmentarium.application.annotations_schema import (
    AnnotationsWithScriptSchema,
    AnnotationsSchema,
)
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.tests.factories.annotation import AnnotationsFactory
from ebl.tests.factories.fragment import FragmentFactory, ScriptFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

COLLECTION = "annotations"


def test_find_by_sign(database, annotations_repository, fragment_repository):
    annotations = AnnotationsFactory.build_batch(3)
    scripts = ScriptFactory.build_batch(3)
    for i, annotation in enumerate(annotations):
        fragment = FragmentFactory.build(
            number=annotation.fragment_number, script=scripts[i]
        )
        fragment_repository.create(fragment)

    sign_query = annotations[0].annotations[0].data.sign_name
    database[COLLECTION].insert_many(
        AnnotationsWithScriptSchema(many=True).dump(annotations)
    )

    results = annotations_repository.find_by_sign(sign_query)

    assert len(results) >= 1
    for i, result in enumerate(results):
        for annotation in result.annotations:
            assert annotation.data.sign_name == sign_query
        assert result.script == scripts[i]


def test_retrieve_all(database, annotations_repository):
    annotations = AnnotationsFactory.build_batch(5)
    database[COLLECTION].insert_many(AnnotationsSchema(many=True).dump(annotations))

    assert annotations_repository.retrieve_all_non_empty() == annotations


def test_retrieve_all_non_empty(database, annotations_repository):
    empty_annotation = AnnotationsFactory.build(annotations=[])
    annotations = AnnotationsFactory.build_batch(4)

    database[COLLECTION].insert_many(
        AnnotationsSchema(many=True).dump([*annotations, empty_annotation])
    )

    assert annotations_repository.retrieve_all_non_empty() == annotations


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
