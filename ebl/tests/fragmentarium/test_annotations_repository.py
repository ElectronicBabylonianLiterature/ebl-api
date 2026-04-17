from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.annotation import PcaClustering
from ebl.fragmentarium.application.annotations_schema import (
    AnnotationsWithScriptSchema,
    AnnotationsSchema,
)
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.tests.factories.annotation import (
    AnnotationDataFactory,
    AnnotationFactory,
    AnnotationsFactory,
)
from ebl.tests.factories.fragment import FragmentFactory, ScriptFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

COLLECTION = "annotations"


def test_find_by_sign(database, annotations_repository, fragment_repository):
    annotations = AnnotationsFactory.build_batch(3)
    scripts = ScriptFactory.build_batch(3)
    expected_scripts = {}
    for i, annotation in enumerate(annotations):
        fragment = FragmentFactory.build(
            number=annotation.fragment_number, script=scripts[i]
        )
        fragment_repository.create(fragment)
        expected_scripts[str(annotation.fragment_number)] = scripts[i]

    sign_query = annotations[0].annotations[0].data.sign_name
    database[COLLECTION].insert_many(
        AnnotationsWithScriptSchema(many=True).dump(annotations)
    )

    results = annotations_repository.find_by_sign(sign_query)

    assert len(results) >= 1
    for result in results:
        for annotation in result.annotations:
            assert annotation.data.sign_name == sign_query
        assert result.script == expected_scripts[str(result.fragment_number)]


def test_find_by_sign_with_script_filter(
    database, annotations_repository, fragment_repository
):
    annotations = AnnotationsFactory.build_batch(3)
    scripts = [
        ScriptFactory.build(period=Period.NEO_ASSYRIAN),
        ScriptFactory.build(period=Period.NEO_BABYLONIAN),
        ScriptFactory.build(period=Period.MIDDLE_ASSYRIAN),
    ]

    for i, annotation in enumerate(annotations):
        fragment = FragmentFactory.build(
            number=annotation.fragment_number, script=scripts[i]
        )
        fragment_repository.create(fragment)

    sign_query = annotations[0].annotations[0].data.sign_name
    target_script = scripts[0]

    database[COLLECTION].insert_many(
        AnnotationsWithScriptSchema(many=True).dump(annotations)
    )

    results = annotations_repository.find_by_sign(
        sign_query, script_filter=target_script.period.long_name
    )

    assert len(results) >= 1
    for result in results:
        assert result.script.period == target_script.period
        for annotation in result.annotations:
            assert annotation.data.sign_name == sign_query


def test_find_by_sign_with_centroids_only(
    database, annotations_repository, fragment_repository
):
    sign_query = "test-sign"

    centroid_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name=sign_query),
        pca_clustering=PcaClustering(
            cluster_id="cluster-1",
            cluster_rank=0,
            form="canonical1",
            is_centroid=True,
            cluster_size=10,
            is_main=True,
        ),
    )
    non_centroid_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name=sign_query),
        pca_clustering=PcaClustering(
            cluster_id="cluster-1",
            cluster_rank=0,
            form="canonical1",
            is_centroid=False,
            cluster_size=10,
            is_main=True,
        ),
    )

    annotations = [
        AnnotationsFactory.build(
            fragment_number=MuseumNumber("X", "100"),
            annotations=[centroid_annotation],
        ),
        AnnotationsFactory.build(
            fragment_number=MuseumNumber("X", "101"),
            annotations=[non_centroid_annotation],
        ),
    ]

    scripts = ScriptFactory.build_batch(2)
    for i, annotation_group in enumerate(annotations):
        fragment = FragmentFactory.build(
            number=annotation_group.fragment_number,
            script=scripts[i],
        )
        fragment_repository.create(fragment)

    database[COLLECTION].insert_many(
        AnnotationsWithScriptSchema(many=True).dump(annotations)
    )

    results = annotations_repository.find_by_sign(sign_query, centroids_only=True)

    assert len(results) >= 1
    for result in results:
        for annotation in result.annotations:
            assert annotation.data.sign_name == sign_query
            assert annotation.pca_clustering is not None
            assert annotation.pca_clustering.is_centroid is True


def test_find_by_sign_with_cluster_id_and_script_filter(
    database, annotations_repository, fragment_repository
):
    sign_query = "test-sign"
    target_cluster_id = "target-cluster"
    other_cluster_id = "other-cluster"

    target_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name=sign_query),
        pca_clustering=PcaClustering(
            cluster_id=target_cluster_id,
            cluster_rank=0,
            form="canonical1",
            is_centroid=True,
            cluster_size=10,
            is_main=True,
        ),
    )
    other_cluster_same_script = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name=sign_query),
        pca_clustering=PcaClustering(
            cluster_id=other_cluster_id,
            cluster_rank=1,
            form="variant1",
            is_centroid=False,
            cluster_size=8,
            is_main=True,
        ),
    )
    target_cluster_other_script = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name=sign_query),
        pca_clustering=PcaClustering(
            cluster_id=target_cluster_id,
            cluster_rank=0,
            form="canonical1",
            is_centroid=False,
            cluster_size=10,
            is_main=True,
        ),
    )

    annotation_group_1 = AnnotationsFactory.build(
        fragment_number=MuseumNumber("X", "200"),
        annotations=[target_annotation],
    )
    annotation_group_2 = AnnotationsFactory.build(
        fragment_number=MuseumNumber("X", "201"),
        annotations=[other_cluster_same_script],
    )
    annotation_group_3 = AnnotationsFactory.build(
        fragment_number=MuseumNumber("X", "202"),
        annotations=[target_cluster_other_script],
    )

    scripts = [
        ScriptFactory.build(period=Period.NEO_ASSYRIAN),
        ScriptFactory.build(period=Period.NEO_BABYLONIAN),
        ScriptFactory.build(period=Period.MIDDLE_ASSYRIAN),
    ]

    fragment_repository.create(
        FragmentFactory.build(
            number=annotation_group_1.fragment_number, script=scripts[0]
        )
    )
    fragment_repository.create(
        FragmentFactory.build(
            number=annotation_group_2.fragment_number, script=scripts[0]
        )
    )
    fragment_repository.create(
        FragmentFactory.build(
            number=annotation_group_3.fragment_number, script=scripts[1]
        )
    )

    database[COLLECTION].insert_many(
        AnnotationsWithScriptSchema(many=True).dump(
            [annotation_group_1, annotation_group_2, annotation_group_3]
        )
    )

    results = annotations_repository.find_by_sign(
        sign_query,
        cluster_id=target_cluster_id,
        script_filter=scripts[0].period.long_name,
    )

    assert len(results) >= 1
    for result in results:
        assert result.script.period == scripts[0].period
        for annotation in result.annotations:
            assert annotation.data.sign_name == sign_query
            assert annotation.pca_clustering is not None
            assert annotation.pca_clustering.cluster_id == target_cluster_id


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
